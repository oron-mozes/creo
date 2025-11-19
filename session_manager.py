"""Session and Runner management for Creo.

This module manages:
- InMemoryRunner lifecycle (one per user)
- Session creation and access
- Shared global memory across all agents (workflow stage, business card, messages)
- Agent-specific memory isolation (internal agent state like onboarding status)

Key Architecture:
- workflow_state.stage (SHARED): Which workflow stage we're in (WorkflowStage enum)
- agent_contexts[agent_name] (AGENT-SPECIFIC): Internal agent state (e.g., OnboardingStatus enum)
"""
from __future__ import annotations

from typing import Optional, Dict, Any, Union, List
from google.adk.runners import InMemoryRunner
from google.genai import types
from datetime import datetime

from workflow_enums import WorkflowStage, OnboardingStatus, ExtractedField


class SessionMemory:
    """Manages memory for a session with both shared and agent-specific contexts."""

    def __init__(self, session_id: str, user_id: str, user_profile: Optional[Dict[str, Any]] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.utcnow()

        # Shared memory - accessible by all agents in this session
        self.shared_context: Dict[str, Any] = {
            'session_id': session_id,
            'user_id': user_id,
            'user_profile': user_profile or {},  # User profile (name from OAuth)
            'messages': [],  # Full conversation history
            'metadata': {},  # Session-level metadata
            'business_card': None,  # Business information from onboarding
            'workflow_state': {
                'stage': None,  # Current workflow stage (WorkflowStage enum or None)
            }
        }

        # Agent-specific memory - isolated per agent
        self.agent_contexts: Dict[str, Dict[str, Any]] = {
            # Example agent-specific contexts:
            # 'onboarding_agent': {'status': OnboardingStatus.COLLECTING},
            # 'creator_finder_agent': {'search_history': [], 'filters': {}},
            # 'campaign_brief_agent': {'briefs': [], 'templates': {}},
        }

    def get_shared_context(self) -> Dict[str, Any]:
        """Get the shared context accessible by all agents."""
        return self.shared_context

    def update_shared_context(self, key: str, value: Any) -> None:
        """Update a value in the shared context."""
        self.shared_context[key] = value

    def get_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """Get or create agent-specific context."""
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = {}
        return self.agent_contexts[agent_name]

    def update_agent_context(self, agent_name: str, key: str, value: Any) -> None:
        """Update a value in agent-specific context."""
        if agent_name not in self.agent_contexts:
            self.agent_contexts[agent_name] = {}
        self.agent_contexts[agent_name][key] = value

    def add_message(self, role: str, content: str, message_id: str = None) -> None:
        """Add a message to the shared conversation history."""
        message = {
            'role': role,
            'content': content,
            'message_id': message_id,
        }
        self.shared_context['messages'].append(message)

    def set_business_card(self, business_card_data: Dict[str, Any]) -> None:
        """Set business card data in shared context."""
        self.shared_context['business_card'] = business_card_data

    def get_business_card(self) -> Optional[Dict[str, Any]]:
        """Get business card data from shared context."""
        return self.shared_context.get('business_card')

    def has_business_card(self) -> bool:
        """Check if business card data exists."""
        return self.shared_context.get('business_card') is not None

    def set_user_profile(self, user_profile: Dict[str, Any]) -> None:
        """Set user profile data in shared context.

        Args:
            user_profile: User profile data with name only
        """
        self.shared_context['user_profile'] = user_profile

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile data from shared context.

        Returns:
            User profile dictionary with name or empty dict
        """
        return self.shared_context.get('user_profile', {})

    def get_workflow_stage(self) -> Optional[WorkflowStage]:
        """Get the current workflow stage.

        Returns:
            WorkflowStage enum value or None if no stage is set
        """
        return self.shared_context['workflow_state'].get('stage')

    def set_workflow_stage(self, stage: Optional[Union[WorkflowStage, str]]) -> None:
        """Set the current workflow stage.

        Args:
            stage: The workflow stage (WorkflowStage enum, string matching enum value, or None)
        """
        # Convert string to enum if needed
        if isinstance(stage, str):
            try:
                stage = WorkflowStage(stage)
            except ValueError:
                raise ValueError(f"Invalid workflow stage: {stage}. Must be one of {[s.value for s in WorkflowStage]}")

        self.shared_context['workflow_state']['stage'] = stage
        stage_value = stage.value if stage else None
        print(f"[SessionMemory] Workflow stage set to: {stage_value}")

    # Onboarding Agent-Specific Methods

    def initialize_onboarding_context(self) -> None:
        """Initialize the onboarding agent's context structure.

        This should be called when onboarding starts to ensure the agent
        has proper memory structure for tracking extractions.
        """
        if 'onboarding_agent' not in self.agent_contexts:
            self.agent_contexts['onboarding_agent'] = {
                'status': OnboardingStatus.COLLECTING,
                'extractions': [],  # List of extraction records
                'extracted_fields': {},  # Current extracted values by field
            }
            print(f"[SessionMemory] Initialized onboarding agent context for session: {self.session_id}")

    def add_extraction(
        self,
        field: Union[ExtractedField, str],
        value: Any,
        message_id: Optional[str] = None,
        source: str = "user_input"
    ) -> None:
        """Record an extracted business card field.

        Args:
            field: The field that was extracted (ExtractedField enum or string)
            value: The extracted value
            message_id: ID of the message where this was extracted
            source: How it was extracted ('user_input', 'google_search', 'inference', etc.)
        """
        # Ensure onboarding context exists
        self.initialize_onboarding_context()

        # Convert string to enum if needed
        if isinstance(field, str):
            try:
                field = ExtractedField(field)
            except ValueError:
                # Allow custom fields that aren't in the enum
                pass

        extraction_record = {
            'field': field.value if isinstance(field, ExtractedField) else field,
            'value': value,
            'message_id': message_id,
            'source': source,
            'timestamp': datetime.utcnow().isoformat(),
        }

        context = self.agent_contexts['onboarding_agent']
        context['extractions'].append(extraction_record)
        context['extracted_fields'][field.value if isinstance(field, ExtractedField) else field] = value

        print(f"[SessionMemory] Onboarding extraction recorded: {field.value if isinstance(field, ExtractedField) else field} = {value} (source: {source})")

    def get_extractions(self) -> List[Dict[str, Any]]:
        """Get all extraction records for this session.

        Returns:
            List of extraction records with field, value, message_id, source, timestamp
        """
        if 'onboarding_agent' not in self.agent_contexts:
            return []
        return self.agent_contexts['onboarding_agent'].get('extractions', [])

    def get_extracted_field(self, field: Union[ExtractedField, str]) -> Optional[Any]:
        """Get the current value of an extracted field.

        Args:
            field: The field to retrieve (ExtractedField enum or string)

        Returns:
            The extracted value or None if not yet extracted
        """
        if 'onboarding_agent' not in self.agent_contexts:
            return None

        field_key = field.value if isinstance(field, ExtractedField) else field
        return self.agent_contexts['onboarding_agent'].get('extracted_fields', {}).get(field_key)

    def has_extracted_field(self, field: Union[ExtractedField, str]) -> bool:
        """Check if a field has been extracted.

        Args:
            field: The field to check (ExtractedField enum or string)

        Returns:
            True if the field has been extracted, False otherwise
        """
        field_key = field.value if isinstance(field, ExtractedField) else field
        if 'onboarding_agent' not in self.agent_contexts:
            return False
        return field_key in self.agent_contexts['onboarding_agent'].get('extracted_fields', {})

    def get_onboarding_status(self) -> Optional[OnboardingStatus]:
        """Get the current onboarding status.

        Returns:
            OnboardingStatus enum value or None if not set
        """
        if 'onboarding_agent' not in self.agent_contexts:
            return None
        return self.agent_contexts['onboarding_agent'].get('status')

    def set_onboarding_status(self, status: Union[OnboardingStatus, str]) -> None:
        """Set the onboarding agent's status.

        Args:
            status: The status (OnboardingStatus enum or string)
        """
        # Ensure onboarding context exists
        self.initialize_onboarding_context()

        # Convert string to enum if needed
        if isinstance(status, str):
            try:
                status = OnboardingStatus(status)
            except ValueError:
                raise ValueError(f"Invalid onboarding status: {status}. Must be one of {[s.value for s in OnboardingStatus]}")

        self.agent_contexts['onboarding_agent']['status'] = status
        print(f"[SessionMemory] Onboarding status set to: {status.value}")

    # Outreach Message Agent-Specific Methods

    def initialize_outreach_context(self) -> None:
        """Initialize the outreach message agent's context structure.

        This should be called when outreach starts to ensure the agent
        has proper memory structure for tracking sent emails and responses.
        """
        if 'outreach_message_agent' not in self.agent_contexts:
            self.agent_contexts['outreach_message_agent'] = {
                'status': 'preparing',  # OutreachStatus enum
                'sent_emails': [],  # List of sent OutreachEmail records
                'responses': [],  # List of InfluencerResponse records
                'current_creator': None,  # Currently targeted creator
            }
            print(f"[SessionMemory] Initialized outreach agent context for session: {self.session_id}")

    def add_outreach_email(self, outreach_email_data: Dict[str, Any]) -> None:
        """Record a sent outreach email.

        Args:
            outreach_email_data: Dictionary with OutreachEmail fields
        """
        self.initialize_outreach_context()

        email_record = {
            'creator_email': outreach_email_data.get('creator_email'),
            'creator_name': outreach_email_data.get('creator_name'),
            'brand_name': outreach_email_data.get('brand_name'),
            'sent_at': datetime.utcnow().isoformat(),
            'email_id': outreach_email_data.get('email_id'),
            'status': 'awaiting_response',  # awaiting_response, interested, not_interested, need_info
        }

        context = self.agent_contexts['outreach_message_agent']
        context['sent_emails'].append(email_record)
        context['status'] = 'email_sent'

        print(f"[SessionMemory] Outreach email recorded: {outreach_email_data.get('creator_name')} ({outreach_email_data.get('creator_email')})")

    def record_influencer_response(self, response_data: Dict[str, Any]) -> None:
        """Record an influencer's response to outreach email.

        Args:
            response_data: Dictionary with InfluencerResponse fields
        """
        self.initialize_outreach_context()

        response_record = {
            'creator_email': response_data.get('creator_email'),
            'creator_name': response_data.get('creator_name'),
            'response_type': response_data.get('response_type'),
            'responded_at': response_data.get('responded_at', datetime.utcnow().isoformat()),
        }

        context = self.agent_contexts['outreach_message_agent']
        context['responses'].append(response_record)
        context['status'] = 'response_received'

        # Update the status of the corresponding sent email
        for email in context['sent_emails']:
            if email['creator_email'] == response_data.get('creator_email'):
                email['status'] = response_data.get('response_type')
                break

        print(f"[SessionMemory] Influencer response recorded: {response_data.get('creator_name')} - {response_data.get('response_type')}")

    def get_outreach_status(self) -> Optional[str]:
        """Get the current outreach status.

        Returns:
            Outreach status string or None if not set
        """
        if 'outreach_message_agent' not in self.agent_contexts:
            return None
        return self.agent_contexts['outreach_message_agent'].get('status')

    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get all sent outreach emails for this session.

        Returns:
            List of sent email records
        """
        if 'outreach_message_agent' not in self.agent_contexts:
            return []
        return self.agent_contexts['outreach_message_agent'].get('sent_emails', [])

    def get_influencer_responses(self) -> List[Dict[str, Any]]:
        """Get all influencer responses for this session.

        Returns:
            List of response records
        """
        if 'outreach_message_agent' not in self.agent_contexts:
            return []
        return self.agent_contexts['outreach_message_agent'].get('responses', [])

    def set_current_creator(self, creator_data: Dict[str, Any]) -> None:
        """Set the currently targeted creator for outreach.

        Args:
            creator_data: Creator information (name, email, etc.)
        """
        self.initialize_outreach_context()
        self.agent_contexts['outreach_message_agent']['current_creator'] = creator_data
        print(f"[SessionMemory] Current creator set: {creator_data.get('name')}")

    def get_current_creator(self) -> Optional[Dict[str, Any]]:
        """Get the currently targeted creator.

        Returns:
            Creator data dictionary or None
        """
        if 'outreach_message_agent' not in self.agent_contexts:
            return None
        return self.agent_contexts['outreach_message_agent'].get('current_creator')


class SessionManager:
    """Manages InMemoryRunners and Sessions for all users.

    Responsibilities:
    - One InMemoryRunner per user_id
    - Multiple sessions per runner
    - Memory management (shared + agent-specific)
    - Session lifecycle
    """

    def __init__(self, root_agent=None):
        # One runner per user
        self._runners: Dict[str, InMemoryRunner] = {}

        # Session memory management
        self._session_memories: Dict[str, SessionMemory] = {}

        # Root agent (will be set from server.py)
        self._root_agent = root_agent

    def set_root_agent(self, root_agent):
        """Set the root agent for creating runners.

        Args:
            root_agent: The root agent instance
        """
        self._root_agent = root_agent

    def get_or_create_runner(self, user_id: str) -> InMemoryRunner:
        """Get existing runner for user or create a new one.

        Args:
            user_id: The user identifier

        Returns:
            InMemoryRunner instance for this user
        """
        if user_id not in self._runners:
            if self._root_agent is None:
                raise ValueError("Root agent not set. Call set_root_agent() first.")
            print(f"[SessionManager] Creating new runner for user: {user_id}")
            self._runners[user_id] = InMemoryRunner(agent=self._root_agent)
        return self._runners[user_id]

    def ensure_session(self, user_id: str, session_id: str, user_profile: Optional[Dict[str, Any]] = None) -> None:
        """Ensure a session exists in the runner.

        Args:
            user_id: The user identifier
            session_id: The session identifier
            user_profile: Optional user profile data (name only)
        """
        runner = self.get_or_create_runner(user_id)
        session_service = runner.session_service

        # Check if session exists
        if hasattr(session_service, "get_session_sync"):
            existing = session_service.get_session_sync(
                app_name=runner.app_name, user_id=user_id, session_id=session_id
            )
        else:
            existing = None

        if existing:
            # Update user profile if provided (in case it changed)
            if user_profile and session_id in self._session_memories:
                self._session_memories[session_id].set_user_profile(user_profile)
            return

        # Create new session
        if hasattr(session_service, "create_session_sync"):
            session_service.create_session_sync(
                app_name=runner.app_name, user_id=user_id, session_id=session_id
            )

        # Initialize session memory
        if session_id not in self._session_memories:
            print(f"[SessionManager] Creating memory for session: {session_id}")
            self._session_memories[session_id] = SessionMemory(session_id, user_id, user_profile)

            # Load business card from persistent storage if available
            # This will be populated by server.py after session is ensured
            print(f"[SessionManager] Session memory created for: {session_id}")

    def get_session_memory(self, session_id: str) -> Optional[SessionMemory]:
        """Get the memory for a specific session.

        Args:
            session_id: The session identifier

        Returns:
            SessionMemory instance or None if session doesn't exist
        """
        return self._session_memories.get(session_id)

    def load_business_card_into_session(self, session_id: str, business_card_data: Optional[Dict[str, Any]]) -> None:
        """Load business card data into session memory.

        Args:
            session_id: The session identifier
            business_card_data: Business card data to load (can be None)
        """
        session_memory = self.get_session_memory(session_id)
        if session_memory and business_card_data:
            session_memory.set_business_card(business_card_data)
            print(f"[SessionManager] Loaded business card into session: {session_id}")

    def run_agent(
        self,
        user_id: str,
        session_id: str,
        message: str,
        user_profile: Optional[Dict[str, Any]] = None
    ):
        """Run the agent with proper session and memory context.

        Args:
            user_id: The user identifier
            session_id: The session identifier
            message: The user's message
            user_profile: Optional user profile data (name only)

        Yields:
            Events from the agent execution
        """
        # Ensure session exists
        self.ensure_session(user_id, session_id, user_profile)

        # Get session memory
        session_memory = self.get_session_memory(session_id)
        if session_memory:
            # Add message to shared memory
            session_memory.add_message('user', message)

        # Set session context for tools to access
        from agents.onboarding_agent.tools import set_session_context
        set_session_context(self, session_id)

        # Get runner and execute
        runner = self.get_or_create_runner(user_id)

        # CRITICAL: Prepend session context to the message so orchestrator can access it
        enhanced_message = self._build_message_with_context(session_id, message)

        # Create message for agent
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=enhanced_message)],
        )

        # Run agent and yield events
        try:
            for event in runner.run(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message,
            ):
                yield event
        except Exception as e:
            # Check if it's a 503 service overload error
            error_message = str(e)
            if '503' in error_message and 'overloaded' in error_message.lower():
                # Yield a fake error event that looks like a normal agent response
                print(f"[SessionManager] ✓ Caught 503 error, yielding friendly error event")
                error_event = types.Event(
                    author="system",
                    content=types.Content(
                        role="model",
                        parts=[types.Part(text=(
                            "⚠️ Our AI service is experiencing high traffic right now. "
                            "This is a temporary issue on Google's side.\n\n"
                            "Please try again in a few minutes, or contact support if this persists.\n\n"
                            "We apologize for the inconvenience!"
                        ))]
                    )
                )
                yield error_event
            else:
                # Re-raise other exceptions
                raise

    def _build_message_with_context(self, session_id: str, user_message: str) -> str:
        """Build a message with session context prepended.

        This allows ALL agents (orchestrator and sub-agents) to see the current
        workflow state and business card status.

        The context is prepended to EVERY user message, ensuring it's visible in
        the conversation history that sub-agents receive when called by the orchestrator.

        Args:
            session_id: The session identifier
            user_message: The user's original message

        Returns:
            Enhanced message with context
        """
        session_memory = self.get_session_memory(session_id)
        if not session_memory:
            return user_message
        user_id = session_memory.user_id

        # Build context header
        context_parts = ["=== SESSION CONTEXT (accessible by all agents) ==="]

        # Add workflow stage
        workflow_stage = session_memory.get_workflow_stage()
        if workflow_stage:
            context_parts.append(f"workflow_state.stage: '{workflow_stage.value}'")
        else:
            context_parts.append("workflow_state.stage: None")

        # Add business card status
        business_card = session_memory.get_business_card()
        if business_card:
            context_parts.append(f"business_card: {business_card}")
        else:
            context_parts.append("business_card: None")

        # Add onboarding status if available
        onboarding_status = session_memory.get_onboarding_status()
        if onboarding_status:
            context_parts.append(f"onboarding_status: '{onboarding_status.value}'")

        context_parts.append("=== END SESSION CONTEXT ===")
        context_parts.append("")  # Empty line
        context_parts.append(f"User message: {user_message}")

        # Add summaries of prior sessions for this user (up to 4 most recent)
        def _truncate(text: str, max_len: int = 200) -> str:
            if text is None:
                return ""
            return text if len(text) <= max_len else text[: max_len - 3] + "..."

        prior_sessions = [
            mem for sid, mem in self._session_memories.items()
            if mem.user_id == user_id and sid != session_id
        ]
        prior_sessions = sorted(prior_sessions, key=lambda m: getattr(m, "created_at", datetime.min), reverse=True)[:4]
        if prior_sessions:
            context_parts.append("")
            context_parts.append("=== PRIOR SESSION SUMMARIES (last 4) ===")
            for idx, mem in enumerate(prior_sessions, start=1):
                messages = mem.get_shared_context().get('messages', [])
                last_user = next((m['content'] for m in reversed(messages) if m.get('role') == 'user'), "")
                last_assistant = next((m['content'] for m in reversed(messages) if m.get('role') == 'assistant'), "")
                bc = mem.get_business_card()
                context_parts.append(
                    f"[Session {idx}] created_at={getattr(mem, 'created_at', '')} "
                    f"msgs={len(messages)} "
                    f"business_card={'yes' if bc else 'no'} "
                    f"last_user=\"{_truncate(last_user)}\" "
                    f"last_assistant=\"{_truncate(last_assistant)}\""
                )
            context_parts.append("=== END PRIOR SESSION SUMMARIES ===")

        # Summarize older messages but keep last N intact
        MAX_CONTEXT_MESSAGES = 20
        messages = session_memory.get_shared_context().get('messages', [])
        summary_text = ""
        if len(messages) > MAX_CONTEXT_MESSAGES:
            older = messages[:-MAX_CONTEXT_MESSAGES]
            # Simple heuristic summary: count roles and include first/last snippets
            user_msgs = [m['content'] for m in older if m.get('role') == 'user']
            assistant_msgs = [m['content'] for m in older if m.get('role') == 'assistant']
            summary_text = [
                "--- Conversation summary of earlier turns ---",
                f"Older user turns: {len(user_msgs)}",
                f"Older assistant turns: {len(assistant_msgs)}",
            ]
            if user_msgs:
                summary_text.append(f"First user msg: {user_msgs[0][:200]}")
            if assistant_msgs:
                summary_text.append(f"First assistant msg: {assistant_msgs[0][:200]}")
            if user_msgs:
                summary_text.append(f"Last user msg in summary: {user_msgs[-1][:200]}")
            if assistant_msgs:
                summary_text.append(f"Last assistant msg in summary: {assistant_msgs[-1][:200]}")
            summary_text.append("--- Recent turns follow ---")
            summary_text = "\n".join(summary_text)

        if summary_text:
            context_parts.append(summary_text)

        enhanced = "\n".join(context_parts)
        print(f"[SessionManager] Enhanced message with context:")
        print(f"  - Workflow stage: {workflow_stage.value if workflow_stage else 'None'}")
        print(f"  - Business card: {'Present' if business_card else 'None'}")
        print(f"  - User message: {user_message[:100]}...")
        if summary_text:
            print(f"  - Summary injected for {len(messages) - MAX_CONTEXT_MESSAGES} earlier messages")
        return enhanced

    def save_assistant_message(
        self,
        session_id: str,
        content: str,
        message_id: str = None
    ) -> None:
        """Save assistant's response to session memory.

        Args:
            session_id: The session identifier
            content: The assistant's response
            message_id: Optional message identifier
        """
        session_memory = self.get_session_memory(session_id)
        if session_memory:
            session_memory.add_message('assistant', content, message_id)

    def get_shared_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get shared context for a session.

        Args:
            session_id: The session identifier

        Returns:
            Shared context dictionary or None
        """
        memory = self.get_session_memory(session_id)
        return memory.get_shared_context() if memory else None

    def get_agent_context(self, session_id: str, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent-specific context for a session.

        Args:
            session_id: The session identifier
            agent_name: The name of the agent

        Returns:
            Agent-specific context dictionary or None
        """
        memory = self.get_session_memory(session_id)
        return memory.get_agent_context(agent_name) if memory else None

    def clear_user_sessions(self, user_id: str) -> None:
        """Clear all sessions for a user.

        Args:
            user_id: The user identifier
        """
        if user_id in self._runners:
            print(f"[SessionManager] Clearing runner for user: {user_id}")
            del self._runners[user_id]

        # Clear session memories for this user
        sessions_to_remove = [
            sid for sid, mem in self._session_memories.items()
            if mem.user_id == user_id
        ]
        for session_id in sessions_to_remove:
            print(f"[SessionManager] Clearing memory for session: {session_id}")
            del self._session_memories[session_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about active runners and sessions.

        Returns:
            Dictionary with runner and session counts
        """
        return {
            'active_runners': len(self._runners),
            'active_sessions': len(self._session_memories),
            'users': list(self._runners.keys()),
        }


# Global singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global SessionManager instance.

    Returns:
        The global SessionManager singleton
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
