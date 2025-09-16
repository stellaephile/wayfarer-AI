import streamlit as st
import json
from datetime import datetime
from vertex_ai_utils import VertexAITripPlanner
from database import db

class ChatInterface:
    def __init__(self):
        self.vertex_ai = VertexAITripPlanner()
    
    def show_chat_interface(self, trip_id, user_id, current_trip_data):
        """Display the interactive chat interface for trip refinement"""
        
        # Initialize chat history in session state if not exists
        if f'chat_history_{trip_id}' not in st.session_state:
            st.session_state[f'chat_history_{trip_id}'] = []
        
        # Load existing chat history from database
        chat_history = db.get_chat_history(trip_id, user_id)
        if chat_history and not st.session_state[f'chat_history_{trip_id}']:
            st.session_state[f'chat_history_{trip_id}'] = chat_history
        
        # Display chat header
        st.subheader("💬 Interactive Trip Refinement")
        st.markdown("Chat with AI to refine your trip plan. Ask for changes like 'Make it more adventurous' or 'Reduce the budget'.")
        
        # Create two columns for chat and trip display
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Chat messages container
            chat_container = st.container()
            
            with chat_container:
                # Display chat history
                for interaction in st.session_state[f'chat_history_{trip_id}']:
                    if interaction['message_type'] == 'user':
                        st.markdown(f"""
                        <div style="background-color: #e3f2fd; padding: 10px; border-radius: 10px; margin: 5px 0; text-align: right;">
                            <strong>You:</strong> {interaction['message_content']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif interaction['message_type'] == 'ai':
                        st.markdown(f"""
                        <div style="background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin: 5px 0;">
                            <strong>AI:</strong> {interaction['ai_response']}
                        </div>
                        """, unsafe_allow_html=True)
            
            # Chat input
            with st.form(f"chat_form_{trip_id}", clear_on_submit=True):
                user_message = st.text_area(
                    "Type your message here...",
                    placeholder="e.g., 'Make it more adventurous', 'Reduce the budget by $200', 'Add more cultural activities'",
                    height=100,
                    key=f"chat_input_{trip_id}"
                )
                
                col_send, col_clear = st.columns([1, 1])
                
                with col_send:
                    send_message = st.form_submit_button("Send Message", type="primary", use_container_width=True)
                
                with col_clear:
                    clear_chat = st.form_submit_button("Clear Chat", type="secondary", use_container_width=True)
            
            # Handle form submissions
            if send_message and user_message.strip():
                self._handle_user_message(trip_id, user_id, user_message.strip(), current_trip_data)
                st.rerun()
            
            if clear_chat:
                st.session_state[f'chat_history_{trip_id}'] = []
                st.rerun()
        
        with col2:
            # Display current trip summary
            self._display_trip_summary(current_trip_data)
    
    def _handle_user_message(self, trip_id, user_id, message, current_trip_data):
        """Handle user message and generate AI response"""
        
        # Save user message to database
        db.save_chat_interaction(trip_id, user_id, 'user', message)
        
        # Add to session state
        st.session_state[f'chat_history_{trip_id}'].append({
            'message_type': 'user',
            'message_content': message,
            'ai_response': None,
            'created_at': datetime.now().isoformat()
        })
        
        # Generate AI response
        try:
            with st.spinner("AI is thinking..."):
                ai_response = self._generate_refinement_response(message, current_trip_data)
            
            # Save AI response to database
            db.save_chat_interaction(trip_id, user_id, 'ai', message, ai_response)
            
            # Add to session state
            st.session_state[f'chat_history_{trip_id}'].append({
                'message_type': 'ai',
                'message_content': message,
                'ai_response': ai_response,
                'created_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            error_response = f"Sorry, I encountered an error: {str(e)}. Please try again."
            st.error(error_response)
            
            # Save error response
            db.save_chat_interaction(trip_id, user_id, 'ai', message, error_response)
            st.session_state[f'chat_history_{trip_id}'].append({
                'message_type': 'ai',
                'message_content': message,
                'ai_response': error_response,
                'created_at': datetime.now().isoformat()
            })
    
    def _generate_refinement_response(self, user_message, current_trip_data):
        """Generate AI response for trip refinement"""
        
        try:
            # Use the new credit-tracked method
            return self.vertex_ai.generate_chat_response(
                user_message=user_message,
                trip_context=current_trip_data,
                user_id=current_trip_data.get('user_id'),
                trip_id=current_trip_data.get('trip_id')
            )
                
        except Exception as e:
            return f"I understand you want to refine your trip. Let me help you with that. (Error: {str(e)})"
    
    def _create_refinement_prompt(self, user_message, current_trip_data):
        """Create a context-aware prompt for trip refinement"""
        
        # Extract key information from current trip
        destination = current_trip_data.get('destination', 'Unknown')
        budget = current_trip_data.get('budget', 0)
        duration = current_trip_data.get('duration', 'Unknown')
        preferences = current_trip_data.get('preferences', 'General travel')
        
        prompt = f"""
You are an expert travel planner helping to refine a trip plan. Be conversational, helpful, and specific.

CURRENT TRIP CONTEXT:
- Destination: {destination}
- Budget: ${budget:,.2f}
- Duration: {duration}
- Preferences: {preferences}

USER REQUEST: "{user_message}"

INSTRUCTIONS:
1. Respond in a conversational, helpful tone
2. Be specific about what changes you can make
3. If the request is about budget, provide specific cost adjustments
4. If about activities, suggest specific alternatives
5. If about accommodations, recommend specific types or areas
6. Keep responses concise but informative (2-3 sentences)
7. Always end with a question to encourage further refinement

RESPONSE FORMAT:
Provide a helpful response that addresses the user's request and offers specific suggestions for improvement.
"""
        
        return prompt
    
    def _get_fallback_response(self, user_message):
        """Provide fallback responses when AI is not available"""
        
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['budget', 'cheaper', 'expensive', 'cost', 'money']):
            return "I can help you adjust the budget! I can suggest more budget-friendly accommodations, free activities, or local dining options. What specific budget changes would you like to make?"
        
        elif any(word in message_lower for word in ['adventure', 'adventurous', 'exciting', 'thrilling']):
            return "Great! I can add more adventurous activities like hiking, water sports, or extreme experiences. What type of adventure activities interest you most?"
        
        elif any(word in message_lower for word in ['culture', 'cultural', 'museum', 'historical']):
            return "I'd love to add more cultural experiences! I can include museum visits, historical sites, local festivals, or cultural workshops. What cultural aspects interest you?"
        
        elif any(word in message_lower for word in ['relax', 'relaxing', 'spa', 'peaceful']):
            return "I can make your trip more relaxing by adding spa visits, beach time, or quiet retreats. Would you like me to focus on wellness activities?"
        
        elif any(word in message_lower for word in ['food', 'restaurant', 'dining', 'cuisine']):
            return "I can enhance your food experience with local restaurants, food tours, cooking classes, or street food adventures. What type of culinary experience interests you?"
        
        else:
            return "I understand you'd like to refine your trip! I can help adjust the budget, activities, accommodations, or dining options. What specific changes would you like to make?"
    
    def _display_trip_summary(self, trip_data):
        """Display a summary of the current trip"""
        st.subheader("📋 Current Trip Summary")
        
        if trip_data:
            st.write(f"**Destination:** {trip_data.get('destination', 'N/A')}")
            st.write(f"**Duration:** {trip_data.get('duration', 'N/A')}")
            st.write(f"**Budget:** ${trip_data.get('budget', 0):,.2f}")
            
            if 'itinerary' in trip_data and trip_data['itinerary']:
                st.write("**Days:**")
                for day in trip_data['itinerary'][:3]:  # Show first 3 days
                    st.write(f"• Day {day.get('day', 'N/A')}: {day.get('day_name', '')}")
            
            if 'accommodations' in trip_data and trip_data['accommodations']:
                st.write("**Accommodations:**")
                for acc in trip_data['accommodations'][:2]:  # Show first 2
                    st.write(f"• {acc.get('name', 'N/A')}")
    
    def get_chat_summary(self, trip_id, user_id):
        """Get a summary of chat interactions for a trip"""
        chat_history = db.get_chat_history(trip_id, user_id)
        
        if not chat_history:
            return "No chat interactions yet."
        
        user_messages = [msg for msg in chat_history if msg['message_type'] == 'user']
        ai_messages = [msg for msg in chat_history if msg['message_type'] == 'ai']
        
        return f"Chat Summary: {len(user_messages)} user messages, {len(ai_messages)} AI responses"