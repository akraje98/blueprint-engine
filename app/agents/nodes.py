import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, cast
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.schemas.agent_state import BlueprintAgentState
from app.services.graph_service import GraphService
from app.services.vector_service import vector_service

class ChecklistItemSchema(BaseModel):
    title: str = Field(..., description="Actionable checklist item or event title (e.g., 'Book Flight HYD to SXR')")
    category: str = Field("general", description="Category: 'flight', 'hotel', 'cab', 'food', 'activity', or 'general'")
    buffer_start_time: str = Field("", description="ISO timestamp when prep/commute/check-in begins (e.g., 4h before intl flight, 2h before domestic flight)")
    start_time: str = Field("", description="ISO timestamp when the actual event starts (if applicable)")
    end_time: str = Field("", description="ISO timestamp when the event finishes (if applicable)")
    booking_url: str = Field("", description="Direct search URL to book this item (e.g., Skyscanner, MakeMyTrip, Booking.com) or empty if none")
    estimated_cost: float = Field(0.0, description="Realistic estimated cost in Indian Rupees (INR)")

class ExtractedPayload(BaseModel):
    intent: str = Field(
        ..., 
        description="Use 'DISCOVERY_FAQ' if user wants to plan a trip/project but key details (dates, origin, group size) are missing. "
                    "Use 'GENERATE_CHECKLIST' when enough details exist to create checklist items/events. "
                    "Use 'SEARCH_PREFERENCE' if only stating preferences."
    )
    assistant_reply: str = Field(..., description="Friendly, concise response to show the user in the chat box")
    discovery_questions: List[str] = Field(
        default_factory=list, 
        description="3-4 short discovery FAQ questions if intent is 'DISCOVERY_FAQ', otherwise empty"
    )
    items: List[ChecklistItemSchema] = Field(
        default_factory=list, 
        description="List of checklist tasks or scheduled events with buffer windows, booking URLs, and INR estimates"
    )
    preference_content: str = Field("", description="Any qualitative human preference extracted (e.g., 'Hates rushed mornings')")

class BlueprintNodes:
    """Contains the concrete functional blocks (nodes) for the BluePrint LangGraph brain."""

    @staticmethod
    async def parsing_router_node(state: BlueprintAgentState) -> Dict[str, Any]:
        """LEVEL 1 & 4 NODE: Fetches Valkey preferences, handles Discovery FAQs, Checklists, Buffers & INR Estimates."""
        print("\n🧠 [Agent Node] Router Engine activated. Analyzing request...")
        
        model = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(ExtractedPayload)
        messages = state.get("messages", [])
        workspace_id = state.get("workspace_id", "default_workspace")
        today_str = datetime.now().strftime("%Y-%m-%d (%A)")
        
        # 1. Fetch existing qualitative preferences from Valkey for this workspace
        saved_prefs = await vector_service.get_workspace_preferences(workspace_id)
        prefs_context = f"Saved User Preferences from Valkey: {saved_prefs}." if saved_prefs else "No prior preferences saved."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are the BluePrint AI Planning Orchestrator. Today's date is {today_str}. "
                       f"{prefs_context} "
                       f"1. If the user asks to plan a trip or major event (e.g., 'Plan a trip to Kashmir') without providing dates, "
                       f"departure city, or group details, set intent='DISCOVERY_FAQ', provide a warm assistant_reply, and ask 3-4 crisp discovery_questions "
                       f"while inviting them to reply freely in plain English. "
                       f"2. If details ARE provided, set intent='GENERATE_CHECKLIST' and generate a complete actionable checklist "
                       f"(flights, hotels, cabs/transport, food, activities) in 'items'. "
                       f"3. For timed events, calculate realistic 'buffer_start_time' (e.g., 4 hours prior for international flights, 2.5 hours for domestic flights, 45 mins for local cabs) and 'end_time'. "
                       f"IMPORTANT: If Saved User Preferences mention hating rushed schedules or wanting leisure/buffer time, widen 'buffer_start_time' by an extra 60 minutes! "
                       f"4. Always provide a helpful 'booking_url' and realistic 'estimated_cost' in INR."),
            ("placeholder", "{messages}")
        ])
        
        chain = prompt | model
        response = cast(ExtractedPayload, await chain.ainvoke({"messages": messages}))
        
        formatted_events = []
        for item in response.items:
            formatted_events.append({
                "title": item.title,
                "category": item.category,
                "buffer_start_time": item.buffer_start_time,
                "start_time": item.start_time,
                "end_time": item.end_time,
                "booking_url": item.booking_url,
                "estimated_cost": item.estimated_cost,
                "actual_cost": 0.0,
                "status": "PENDING"
            })
            
        updates = {
            "current_intent": response.intent,
            "assistant_reply": response.assistant_reply,
            "discovery_questions": response.discovery_questions,
            "extracted_events": formatted_events,
            "extracted_preferences": [] if not response.preference_content else [response.preference_content]
        }
        
        print(f"✅ [Agent Node] Intent: {response.intent} | Items generated: {len(formatted_events)}")
        return updates

    @staticmethod
    async def conflict_auditor_node(state: BlueprintAgentState) -> Dict[str, Any]:
        """LEVEL 2 NODE: Checks Neo4j for overlapping buffer/event time windows across all generated items."""
        print("\n🔍 [Agent Node] Conflict Auditor Engine activated. Auditing time windows...")
        
        events = state.get("extracted_events", [])
        workspace_id = state.get("workspace_id", "default_workspace")
        
        if not events:
            return {"audit_report": {"has_conflict": False, "reason": "No timed items to validate."}}
            
        for evt in events:
            b_start = evt.get("buffer_start_time", "")
            end_t = evt.get("end_time", "")
            if b_start and end_t:
                conflict = await GraphService.check_time_conflict(workspace_id, b_start, end_t)
                if conflict:
                    conflict_title = conflict.get("title", "Existing event")
                    print(f"⚠️ [Agent Node] Window clash between '{evt['title']}' and '{conflict_title}'!")
                    return {
                        "audit_report": {
                            "has_conflict": True,
                            "reason": f"Time/buffer overlap detected in workspace '{workspace_id}': '{evt['title']}' ({b_start} to {end_t}) overlaps with '{conflict_title}'."
                        }
                    }
                    
        print("✅ [Agent Node] All checklist items and buffer windows verified clear.")
        return {
            "audit_report": {
                "has_conflict": False,
                "reason": f"All {len(events)} items verified clear inside workspace '{workspace_id}'."
            }
        }

    @staticmethod
    async def persistence_node(state: BlueprintAgentState) -> Dict[str, Any]:
        """LEVEL 2 & 3 NODE: Saves checklist/timeline items to Neo4j and preference vectors to Valkey."""
        print("\n💾 [Agent Node] Persistence Engine activated. Saving to Neo4j and Valkey...")
        
        workspace_id = state.get("workspace_id", "default_workspace")
        events = state.get("extracted_events", [])
        preferences = state.get("extracted_preferences", [])
        saved_events = []

        for evt in events:
            event_id = f"evt_{uuid.uuid4()}"
            node_props = {
                "event_id": event_id,
                "workspace_id": workspace_id,
                "title": evt.get("title", "Untitled Item"),
                "category": evt.get("category", "general"),
                "buffer_start_time": evt.get("buffer_start_time", ""),
                "start_time": evt.get("start_time", ""),
                "end_time": evt.get("end_time", ""),
                "booking_url": evt.get("booking_url", ""),
                "estimated_cost": float(evt.get("estimated_cost", 0.0)),
                "actual_cost": 0.0,
                "status": "PENDING"
            }
            created_node = await GraphService.create_node(label="TimelineEvent", properties=node_props)
            saved_events.append(created_node)
            print(f"🕸️ [Neo4j] Saved Checklist/Event '{node_props['title']}' (Est: ₹{node_props['estimated_cost']})")

        for pref_text in preferences:
            pref_id = await vector_service.store_preference(workspace_id=workspace_id, content=pref_text)
            print(f"🎯 [Valkey] Vectorized & saved preference '{pref_text}' (ID: {pref_id})")

        return {"extracted_events": saved_events}
