import os
import uuid
from datetime import datetime
from typing import Dict, Any, cast
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.schemas.agent_state import BlueprintAgentState
from app.services.graph_service import GraphService
from app.services.vector_service import vector_service

class ExtractedPayload(BaseModel):
    intent: str = Field(..., description="The user's intent: 'CREATE_EVENT', 'SEARCH_PREFERENCE', or 'UNKNOWN'")
    event_title: str = Field("", description="Title of the timeline task or event if found")
    start_time: str = Field("", description="ISO timestamp string of when the event begins if specified")
    preference_content: str = Field("", description="Any raw human qualitative preference strings extracted")

class BlueprintNodes:
    """Contains the concrete functional blocks (nodes) for the BluePrint LangGraph brain."""

    @staticmethod
    async def parsing_router_node(state: BlueprintAgentState) -> Dict[str, Any]:
        """LEVEL 1 & 4 NODE: Extracts structured event and preference payloads from user text."""
        print("\n🧠 [Agent Node] Router Engine activated. Parsing user text context...")
        
        model = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(ExtractedPayload)
        messages = state.get("messages", [])
        today_str = datetime.now().strftime("%Y-%m-%d (%A)")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"You are the primary Parsing Router for the BluePrint engine. "
                       f"Today's current date is {today_str}. "
                       f"Read user requests and extract structured intents, chronological ISO timestamps "
                       f"(defaulting to the upcoming occurrence relative to today's date), "
                       f"or qualitative preference details cleanly."),
            ("placeholder", "{messages}")
        ])
        
        chain = prompt | model
        response = cast(ExtractedPayload, await chain.ainvoke({"messages": messages}))
        
        updates = {
            "current_intent": response.intent,
            "extracted_events": [] if not response.event_title else [{
                "title": response.event_title,
                "start_time": response.start_time,
                "status": "PENDING"
            }],
            "extracted_preferences": [] if not response.preference_content else [response.preference_content]
        }
        
        print(f"✅ [Agent Node] Extracted Intent: {response.intent}")
        return updates

    @staticmethod
    async def conflict_auditor_node(state: BlueprintAgentState) -> Dict[str, Any]:
        """LEVEL 2 NODE: Queries Neo4j within the user's workspace to catch timeline clashes."""
        print("\n🔍 [Agent Node] Conflict Auditor Engine activated. Querying Neo4j matrix...")
        
        events = state.get("extracted_events", [])
        workspace_id = state.get("workspace_id", "default_workspace")
        
        if not events:
            return {"audit_report": {"has_conflict": False, "reason": "No active events to validate."}}
            
        target_event = events[0]
        target_time = target_event.get("start_time", "")
        
        # Query Neo4j for an existing event at the same time in the SAME workspace
        existing_conflict = await GraphService.check_time_conflict(workspace_id, target_time)
        
        if existing_conflict:
            conflict_title = existing_conflict.get("title", "Another event")
            print(f"⚠️ [Agent Node] Conflict found with '{conflict_title}' at {target_time}!")
            return {
                "audit_report": {
                    "has_conflict": True,
                    "reason": f"Time clash detected in workspace '{workspace_id}': '{conflict_title}' is already scheduled at {target_time}."
                }
            }
            
        print("✅ [Agent Node] Graph matrix audit complete. Status: Clear.")
        return {
            "audit_report": {
                "has_conflict": False,
                "reason": f"Timeline slot '{target_time}' verified clear inside workspace '{workspace_id}'."
            }
        }

    @staticmethod
    async def persistence_node(state: BlueprintAgentState) -> Dict[str, Any]:
        """LEVEL 2 & 3 NODE: Saves conflict-free events to Neo4j and preference vectors to Valkey."""
        print("\n💾 [Agent Node] Persistence Engine activated. Writing to Neo4j and Valkey...")
        
        workspace_id = state.get("workspace_id", "default_workspace")
        events = state.get("extracted_events", [])
        preferences = state.get("extracted_preferences", [])
        saved_events = []

        # 1. Write Events to Neo4j with unique UUIDs
        for evt in events:
            event_id = f"evt_{uuid.uuid4()}"
            node_props = {
                "event_id": event_id,
                "workspace_id": workspace_id,
                "title": evt.get("title", "Untitled Event"),
                "start_time": evt.get("start_time", ""),
                "status": "CONFIRMED"
            }
            created_node = await GraphService.create_node(label="TimelineEvent", properties=node_props)
            saved_events.append(created_node)
            print(f"🕸️ [Neo4j] Saved TimelineEvent '{node_props['title']}' (ID: {event_id})")

        # 2. Write Preferences as 1536-dim Vectors to Valkey with unique UUIDs
        for pref_text in preferences:
            pref_id = await vector_service.store_preference(workspace_id=workspace_id, content=pref_text)
            print(f"🎯 [Valkey] Vectorized & saved preference '{pref_text}' (ID: {pref_id})")

        return {"extracted_events": saved_events}
