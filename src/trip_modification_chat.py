import streamlit as st
import json
from datetime import datetime
from vertex_ai_utils import VertexAITripPlanner
from cloudsql_database_config import get_database
db = get_database()

class TripModificationChat:
    def __init__(self):
        self.vertex_ai = VertexAITripPlanner()
    
    def show_modification_interface(self, trip_id, user_id, current_trip_data):
        """Display the interactive trip modification interface"""
        
        # Initialize session state for this trip
        if f'modification_mode_{trip_id}' not in st.session_state:
            st.session_state[f'modification_mode_{trip_id}'] = False
        
        if f'pending_changes_{trip_id}' not in st.session_state:
            st.session_state[f'pending_changes_{trip_id}'] = []
        
        # Load existing chat history
        chat_history = db.get_chat_history(trip_id, user_id)
        if f'chat_history_{trip_id}' not in st.session_state:
            st.session_state[f'chat_history_{trip_id}'] = chat_history
        
        # Header with trip info
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; color: white;">
            <h2 style="margin: 0; color: white;">🗺️ Trip Modification Center</h2>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Chat with AI to refine your trip plan</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Trip summary card
        self._display_trip_summary_card(current_trip_data)
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Chat interface
            self._display_chat_interface(trip_id, user_id, current_trip_data)
        
        with col2:
            # Trip details and modification controls
            self._display_trip_details_sidebar(trip_id, user_id, current_trip_data)
    
    def _display_trip_summary_card(self, trip_data):
        """Display trip summary in a card format"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Destination",
                trip_data.get('destination', 'N/A'),
                help="Your travel destination"
            )
        
        with col2:
            currency_symbol = trip_data.get('currency_symbol', '$')
            st.metric(
                "Budget",
                f"{currency_symbol}{trip_data.get('budget', 0):,.0f}",
                help="Total trip budget"
            )
        
        with col3:
            st.metric(
                "Duration",
                trip_data.get('duration', 'N/A'),
                help="Trip duration"
            )
        
        with col4:
            st.metric(
                "Status",
                "Active",
                help="Trip modification status"
            )
    
    def _display_chat_interface(self, trip_id, user_id, current_trip_data):
        """Display the chat interface"""
        st.subheader("💬 Chat with AI Assistant")
        st.markdown("Ask me to modify your trip! I can help with budget adjustments, activity changes, accommodation updates, and more.")
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Display chat history
            for interaction in st.session_state[f'chat_history_{trip_id}']:
                if interaction['message_type'] == 'user':
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 12px; border-radius: 12px; margin: 8px 0; border-left: 4px solid #2196f3;">
                        <div style="font-weight: 600; color: #1976d2; margin-bottom: 4px;">You</div>
                        <div style="color: #333;">{interaction['message_content']}</div>
                        <div style="font-size: 0.8rem; color: #666; margin-top: 4px;">{interaction.get('created_at', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif interaction['message_type'] == 'ai':
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%); padding: 12px; border-radius: 12px; margin: 8px 0; border-left: 4px solid #4caf50;">
                        <div style="font-weight: 600; color: #388e3c; margin-bottom: 4px;">🤖 AI Assistant</div>
                        <div style="color: #333;">{interaction['ai_response']}</div>
                        <div style="font-size: 0.8rem; color: #666; margin-top: 4px;">{interaction.get('created_at', '')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chat input form
        with st.form(f"chat_form_{trip_id}", clear_on_submit=True):
            user_message = st.text_area(
                "Type your message here...",
                placeholder="e.g., 'Make it more adventurous', 'Reduce the budget by $200', 'Add more cultural activities', 'Change the accommodation to luxury'",
                height=100,
                key=f"chat_input_{trip_id}"
            )
            
            col_send, col_clear, col_finalize = st.columns([1, 1, 1])
            
            with col_send:
                send_message = st.form_submit_button("💬 Send", type="primary", use_container_width=True)
            
            with col_clear:
                clear_chat = st.form_submit_button("🗑️ Clear", type="secondary", use_container_width=True)
            
            with col_finalize:
                finalize_changes = st.form_submit_button("✅ Finalize", type="primary", use_container_width=True)
        
        # Handle form submissions
        if send_message and user_message.strip():
            self._handle_user_message(trip_id, user_id, user_message.strip(), current_trip_data)
            st.rerun()
        
        if clear_chat:
            st.session_state[f'chat_history_{trip_id}'] = []
            st.rerun()
        
        if finalize_changes:
            self._handle_finalize_changes(trip_id, user_id, current_trip_data)
            st.rerun()
    
    def _display_trip_details_sidebar(self, trip_id, user_id, current_trip_data):
        """Display trip details and modification controls in sidebar"""
        st.subheader("📋 Current Trip Details")
        
        # Quick trip overview
        with st.expander("🗺️ Trip Overview", expanded=True):
            st.write(f"**Destination:** {current_trip_data.get('destination', 'N/A')}")
            st.write(f"**Duration:** {current_trip_data.get('duration', 'N/A')}")
            currency_symbol = current_trip_data.get('currency_symbol', '$')
            st.write(f"**Budget:** {currency_symbol}{current_trip_data.get('budget', 0):,.2f}")
            st.write(f"**Preferences:** {current_trip_data.get('preferences', 'N/A')}")
        
        # Itinerary preview
        if 'itinerary' in current_trip_data and current_trip_data['itinerary']:
            with st.expander("🧳 Itinerary Preview", expanded=False):
                for day in current_trip_data['itinerary'][:3]:  # Show first 3 days
                    if isinstance(day, dict):
                        st.write(f"**Day {day.get('day', 'N/A')}:** {day.get('day_name', '')}")
                        if 'activities' in day:
                            for activity in day['activities'][:2]:  # Show first 2 activities
                                st.write(f"• {activity}")
        
        # Accommodations preview
        if 'accommodations' in current_trip_data and current_trip_data['accommodations']:
            with st.expander("🏨 Accommodations", expanded=False):
                for acc in current_trip_data['accommodations'][:2]:  # Show first 2
                    st.write(f"**{acc.get('name', 'N/A')}**")
                    st.write(f"💰 {acc.get('price_range', 'Price not available')}")
        
        # Modification suggestions
        st.subheader("💡 Quick Suggestions")
        
        suggestion_buttons = [
            ("💰 Adjust Budget", "Make the trip more budget-friendly"),
            ("🎯 Add Adventure", "Include more adventurous activities"),
            ("🏛️ Cultural Focus", "Add more cultural experiences"),
            ("🍽️ Food Experience", "Enhance dining recommendations"),
            ("🏨 Upgrade Stay", "Suggest better accommodations"),
            ("🧳 Reschedule", "Adjust the itinerary timing")
        ]
        
        for button_text, suggestion in suggestion_buttons:
            if st.button(button_text, key=f"suggestion_{button_text}_{trip_id}", use_container_width=True):
                self._handle_suggestion_click(trip_id, user_id, suggestion, current_trip_data)
                st.rerun()
        
        # Credit usage info
        self._display_credit_info(user_id)
    
    def _handle_user_message(self, trip_id, user_id, message, current_trip_data):
        """Handle user message and generate AI response"""
        
        # Save user message to database
        db.save_chat_interaction(trip_id, user_id, 'user', message)
        
        # Add to session state
        st.session_state[f'chat_history_{trip_id}'].append({
            'message_type': 'user',
            'message_content': message,
            'ai_response': None,
            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Generate AI response
        try:
            with st.spinner("🤖 AI is thinking..."):
                ai_response = self.vertex_ai.generate_chat_response(
                    user_message=message,
                    trip_context=current_trip_data,
                    user_id=user_id,
                    trip_id=trip_id
                )
            
            # Calculate credits used
            credits_used = self.vertex_ai.calculate_chat_credits(message, len(ai_response))
            
            # Save AI response to database
            db.save_chat_interaction(trip_id, user_id, 'ai', message, ai_response, credits_used)
            
            # Add to session state
            st.session_state[f'chat_history_{trip_id}'].append({
                'message_type': 'ai',
                'message_content': message,
                'ai_response': ai_response,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # Track credits
            db.add_credit_transaction(
                user_id, trip_id, 'usage', credits_used, 
                f"Chat interaction: {message[:50]}..."
            )
            
        except Exception as e:
            error_response = f"Sorry, I encountered an error: {str(e)}. Please try again."
            st.error(error_response)
            
            # Save error response
            db.save_chat_interaction(trip_id, user_id, 'ai', message, error_response)
            st.session_state[f'chat_history_{trip_id}'].append({
                'message_type': 'ai',
                'message_content': message,
                'ai_response': error_response,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    def _handle_suggestion_click(self, trip_id, user_id, suggestion, current_trip_data):
        """Handle suggestion button clicks"""
        self._handle_user_message(trip_id, user_id, suggestion, current_trip_data)
    
    def _handle_finalize_changes(self, trip_id, user_id, current_trip_data):
        """Handle finalizing changes to the trip"""
        st.session_state[f'modification_mode_{trip_id}'] = True
        
        # Show finalization options
        st.success("🎉 Ready to finalize your changes!")
        
        # Create a form for finalizing changes
        with st.form(f"finalize_form_{trip_id}"):
            st.subheader("📝 Finalize Trip Modifications")
            
            # Show summary of changes
            st.write("**Summary of modifications:**")
            chat_history = st.session_state[f'chat_history_{trip_id}']
            if chat_history:
                st.write(f"- {len(chat_history)} chat interactions")
                st.write("- AI has provided recommendations based on your requests")
            
            # Options for finalization
            finalization_option = st.radio(
                "How would you like to proceed?",
                [
                    "Apply AI recommendations to the trip",
                    "Keep current trip as is",
                    "Generate a completely new trip based on our conversation"
                ]
            )
            
            # Additional notes
            notes = st.text_area(
                "Additional notes (optional)",
                placeholder="Any specific requirements or notes for the final trip..."
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                confirm_finalize = st.form_submit_button("✅ Confirm & Apply Changes", type="primary")
            
            with col2:
                cancel_finalize = st.form_submit_button("❌ Cancel", type="secondary")
        
        if confirm_finalize:
            self._apply_trip_modifications(trip_id, user_id, current_trip_data, finalization_option, notes)
            st.rerun()
        
        if cancel_finalize:
            st.info("Finalization cancelled.")
    
    def _apply_trip_modifications(self, trip_id, user_id, current_trip_data, finalization_option, notes):
        """Apply the modifications to the trip"""
        try:
            if finalization_option == "Apply AI recommendations to the trip":
                # Generate updated trip based on chat history
                with st.spinner("🤖 Generating updated trip based on your requests..."):
                    updated_trip_data = self._generate_updated_trip_from_chat(trip_id, user_id, current_trip_data)
                
                if updated_trip_data:
                    # Save the modification
                    db.save_trip_modification(
                        trip_id, user_id, "chat_based_update", 
                        current_trip_data, updated_trip_data, 
                        f"AI recommendations applied based on chat: {notes}", 0
                    )
                    
                    # Update the trip in database
                    success, message = db.update_trip(
                        trip_id, user_id, 
                        ai_suggestions=json.dumps(updated_trip_data)
                    )
                    
                    if success:
                        st.success("✅ Trip updated successfully with AI recommendations!")
                        st.balloons()  # Celebration animation
                        
                        # Clear the modification mode and redirect
                        if f'modification_mode_{trip_id}' in st.session_state:
                            del st.session_state[f'modification_mode_{trip_id}']
                        if 'modification_mode' in st.session_state:
                            del st.session_state.modification_mode
                        if 'modification_trip_id' in st.session_state:
                            del st.session_state.modification_trip_id
                        
                        # Show updated trip details
                        st.subheader("📋 Updated Trip Details")
                        self._display_updated_trip_summary(updated_trip_data)
                        
                        # Add a button to view the updated trip
                        if st.button("👁️ View Updated Trip in My Trips", type="primary"):
                            st.session_state.trip_planner_page = "📚 My Trips"
                            st.rerun()
                    else:
                        st.error(f"❌ Error updating trip: {message}")
                else:
                    st.warning("⚠️ No significant changes were made to the trip.")
            
            elif finalization_option == "Generate a completely new trip based on our conversation":
                # Generate a completely new trip
                with st.spinner("🤖 Generating completely new trip based on our conversation..."):
                    self._generate_new_trip_from_chat(trip_id, user_id, current_trip_data, notes)
            
            else:
                st.info("✅ Trip kept as is. No changes applied.")
                
        except Exception as e:
            st.error(f"❌ Error applying modifications: {str(e)}")
            import traceback
            st.error(f"Debug info: {traceback.format_exc()}")
    
    def _display_updated_trip_summary(self, updated_trip_data):
        """Display a summary of the updated trip"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Destination", updated_trip_data.get('destination', 'N/A'))
        
        with col2:
            currency_symbol = updated_trip_data.get('currency_symbol', '$')
            st.metric("Budget", f"{currency_symbol}{updated_trip_data.get('budget', 0):,.0f}")
        
        with col3:
            st.metric("Duration", updated_trip_data.get('duration', 'N/A'))
        
        # Show key changes
        if 'activities' in updated_trip_data and updated_trip_data['activities']:
            st.subheader("🎯 Updated Activities")
            for activity in updated_trip_data['activities'][:3]:  # Show first 3
                if isinstance(activity, dict):
                    st.write(f"• **{activity.get('name', 'Activity')}** - {activity.get('description', '')}")
        
        if 'accommodations' in updated_trip_data and updated_trip_data['accommodations']:
            st.subheader("🏨 Updated Accommodations")
            for acc in updated_trip_data['accommodations'][:2]:  # Show first 2
                if isinstance(acc, dict):
                    st.write(f"• **{acc.get('name', 'Accommodation')}** - {acc.get('price_range', '')}")
    
    def _generate_updated_trip_from_chat(self, trip_id, user_id, current_trip_data):
        """Generate updated trip data based on chat history"""
        try:
            # Get chat history
            chat_history = st.session_state[f'chat_history_{trip_id}']
            
            if not chat_history:
                st.warning("No chat history found. Using simple modifications.")
                return self._apply_simple_modifications(current_trip_data, ["General improvements"])
            
            # Create a summary of user requests
            user_requests = []
            for interaction in chat_history:
                if interaction['message_type'] == 'user':
                    user_requests.append(interaction['message_content'])
            
            if not user_requests:
                st.warning("No user requests found. Using simple modifications.")
                return self._apply_simple_modifications(current_trip_data, ["General improvements"])
            
            # Create a prompt for updating the trip
            update_prompt = self._create_trip_update_prompt(current_trip_data, user_requests)
            
            # Generate updated trip using AI
            if self.vertex_ai.is_configured and self.vertex_ai.model:
                try:
                    generation_config = GenerationConfig(
                        max_output_tokens=4096,  # Increased for complete responses
                        temperature=0.7,
                        top_p=0.95,
                    )
                    
                    response = self.vertex_ai.model.generate_content(update_prompt, generation_config=generation_config)
                    if response and response.text:
                        # Clean the response text
                        cleaned_text = response.text.strip()
                        
                        # Try to extract JSON from the response
                        if cleaned_text.startswith('```json'):
                            cleaned_text = cleaned_text[7:]
                        if cleaned_text.endswith('```'):
                            cleaned_text = cleaned_text[:-3]
                        
                        # Parse the updated trip data
                        updated_data = json.loads(cleaned_text)
                        
                        # Validate the updated data
                        if self._validate_trip_data(updated_data):
                            st.success("✅ AI successfully generated updated trip!")
                            return updated_data
                        else:
                            st.warning("⚠️ AI response validation failed. Using simple modifications.")
                            return self._apply_simple_modifications(current_trip_data, user_requests)
                    else:
                        st.warning("⚠️ Empty AI response. Using simple modifications.")
                        return self._apply_simple_modifications(current_trip_data, user_requests)
                        
                except json.JSONDecodeError as e:
                    st.warning(f"⚠️ Failed to parse AI response as JSON: {str(e)}. Using simple modifications.")
                    return self._apply_simple_modifications(current_trip_data, user_requests)
                except Exception as e:
                    st.warning(f"⚠️ AI generation failed: {str(e)}. Using simple modifications.")
                    return self._apply_simple_modifications(current_trip_data, user_requests)
            else:
                st.info("ℹ️ AI not configured. Using simple modifications.")
                return self._apply_simple_modifications(current_trip_data, user_requests)
            
        except Exception as e:
            st.error(f"Error generating updated trip: {str(e)}")
            return self._apply_simple_modifications(current_trip_data, ["General improvements"])
    
    def _validate_trip_data(self, trip_data):
        """Validate that the trip data has the required structure"""
        try:
            required_fields = ['destination', 'budget', 'itinerary']
            for field in required_fields:
                if field not in trip_data:
                    return False
            
            # Check if itinerary is a list
            if not isinstance(trip_data.get('itinerary'), list):
                return False
            
            return True
        except Exception:
            return False
    
    def _create_trip_update_prompt(self, current_trip_data, user_requests):
        """Create a prompt for updating the trip based on user requests"""
        requests_summary = "\n".join([f"- {req}" for req in user_requests])
        
        prompt = f"""
You are an expert travel planner. Update the following trip plan based on the user's requests.

CURRENT TRIP DATA:
{json.dumps(current_trip_data, indent=2)}

USER REQUESTS:
{requests_summary}

INSTRUCTIONS:
1. Update the trip plan to address the user's requests
2. Maintain the same JSON structure
3. Keep the same destination, dates, and budget unless specifically requested to change
4. Make realistic and practical modifications
5. Ensure all changes are coherent and well-integrated

RESPONSE FORMAT:
Return ONLY the updated JSON object with the same structure as the current trip data.
"""
        
        return prompt
    
    def _apply_simple_modifications(self, current_trip_data, user_requests):
        """Apply simple modifications to the trip data"""
        updated_data = current_trip_data.copy()
        
        # Ensure activities list exists
        if 'activities' not in updated_data:
            updated_data['activities'] = []
        
        # Simple keyword-based modifications
        for request in user_requests:
            request_lower = request.lower()
            
            if any(word in request_lower for word in ['budget', 'cheaper', 'expensive', 'cost']):
                # Adjust budget-related items
                if 'accommodations' in updated_data:
                    for acc in updated_data['accommodations']:
                        if 'price_range' in acc:
                            # Make prices more budget-friendly
                            acc['price_range'] = acc['price_range'].replace('$', 'Budget-friendly')
                
                # Add budget tips
                if 'tips' not in updated_data:
                    updated_data['tips'] = []
                updated_data['tips'].append("Look for local street food and free walking tours to save money")
            
            elif any(word in request_lower for word in ['adventure', 'adventurous', 'exciting']):
                # Add adventure activities
                adventure_activities = [
                    {
                        "name": "Mountain Hiking Adventure",
                        "type": "Adventure",
                        "duration": "Full Day",
                        "cost": "$50-100",
                        "description": "Exciting mountain hiking with scenic views",
                        "rating": 4.7,
                        "best_time": "Early Morning"
                    },
                    {
                        "name": "Water Sports Experience",
                        "type": "Adventure",
                        "duration": "Half Day",
                        "cost": "$30-60",
                        "description": "Thrilling water sports activities",
                        "rating": 4.5,
                        "best_time": "Afternoon"
                    }
                ]
                
                for activity in adventure_activities:
                    if activity not in updated_data['activities']:
                        updated_data['activities'].append(activity)
            
            elif any(word in request_lower for word in ['culture', 'cultural', 'museum', 'historical']):
                # Add cultural activities
                cultural_activities = [
                    {
                        "name": "Cultural Heritage Tour",
                        "type": "Cultural",
                        "duration": "3-4 hours",
                        "cost": "$25-40",
                        "description": "Immersive cultural heritage experience",
                        "rating": 4.6,
                        "best_time": "Morning"
                    },
                    {
                        "name": "Local Art Workshop",
                        "type": "Cultural",
                        "duration": "2-3 hours",
                        "cost": "$20-35",
                        "description": "Hands-on local art and craft workshop",
                        "rating": 4.4,
                        "best_time": "Afternoon"
                    }
                ]
                
                for activity in cultural_activities:
                    if activity not in updated_data['activities']:
                        updated_data['activities'].append(activity)
            
            elif any(word in request_lower for word in ['food', 'restaurant', 'dining', 'cuisine']):
                # Add food experiences
                if 'restaurants' not in updated_data:
                    updated_data['restaurants'] = []
                
                food_experiences = [
                    {
                        "name": "Local Food Market Tour",
                        "cuisine": "Local Street Food",
                        "price_range": "$15-25 per person",
                        "rating": 4.8,
                        "specialties": ["Authentic local dishes", "Fresh ingredients"],
                        "location": "Historic market area",
                        "reservation_required": False
                    },
                    {
                        "name": "Cooking Class Experience",
                        "cuisine": "Interactive Cooking",
                        "price_range": "$40-60 per person",
                        "rating": 4.7,
                        "specialties": ["Learn local recipes", "Hands-on cooking"],
                        "location": "Cooking school",
                        "reservation_required": True
                    }
                ]
                
                for restaurant in food_experiences:
                    if restaurant not in updated_data['restaurants']:
                        updated_data['restaurants'].append(restaurant)
            
            elif any(word in request_lower for word in ['luxury', 'upgrade', 'premium']):
                # Add luxury options
                if 'accommodations' in updated_data:
                    for acc in updated_data['accommodations']:
                        if 'price_range' in acc:
                            acc['price_range'] = acc['price_range'].replace('Budget-friendly', 'Luxury')
                        if 'amenities' in acc:
                            acc['amenities'].extend(['Spa', 'Concierge', 'Room Service', 'Premium WiFi'])
                
                # Add luxury activities
                luxury_activities = [
                    {
                        "name": "Private Guided Tour",
                        "type": "Luxury",
                        "duration": "Full Day",
                        "cost": "$200-400",
                        "description": "Exclusive private guided experience",
                        "rating": 4.9,
                        "best_time": "All Day"
                    }
                ]
                
                for activity in luxury_activities:
                    if activity not in updated_data['activities']:
                        updated_data['activities'].append(activity)
        
        # Add a note about modifications
        if 'tips' not in updated_data:
            updated_data['tips'] = []
        updated_data['tips'].append("This trip has been customized based on your preferences")
        
        return updated_data
    
    def _generate_new_trip_from_chat(self, trip_id, user_id, current_trip_data, notes):
        """Generate a completely new trip based on chat conversation"""
        try:
            # Get chat history
            chat_history = st.session_state[f'chat_history_{trip_id}']
            
            # Create a summary of the conversation
            conversation_summary = self._create_conversation_summary(chat_history)
            
            # Generate new trip using the original trip planner
            new_trip_data = self.vertex_ai.generate_trip_suggestions(
                destination=current_trip_data.get('destination', 'Unknown'),
                start_date=current_trip_data.get('start_date', '2024-01-01'),
                end_date=current_trip_data.get('end_date', '2024-01-07'),
                budget=current_trip_data.get('budget', 1000),
                preferences=f"{current_trip_data.get('preferences', '')} | Chat modifications: {conversation_summary} | Notes: {notes}",
                currency=current_trip_data.get('currency', 'USD'),
                currency_symbol=current_trip_data.get('currency_symbol', '$')
            )
            
            if new_trip_data:
                # Save the modification
                db.save_trip_modification(
                    trip_id, user_id, "complete_regeneration", 
                    current_trip_data, new_trip_data, 
                    f"New trip generated based on chat conversation: {notes}", 0
                )
                
                # Update the trip in database
                success, message = db.update_trip(
                    trip_id, user_id, 
                    ai_suggestions=json.dumps(new_trip_data)
                )
                
                if success:
                    st.success("✅ New trip generated successfully based on our conversation!")
                else:
                    st.error(f"❌ Error updating trip: {message}")
            else:
                st.error("❌ Failed to generate new trip.")
                
        except Exception as e:
            st.error(f"❌ Error generating new trip: {str(e)}")
    
    def _create_conversation_summary(self, chat_history):
        """Create a summary of the chat conversation"""
        user_messages = [msg['message_content'] for msg in chat_history if msg['message_type'] == 'user']
        return " | ".join(user_messages[:5])  # Take first 5 user messages
    
    def _display_credit_info(self, user_id):
        """Display credit usage information"""
        st.subheader("💳 Credit Usage")
        
        credits_info = db.get_user_credits(user_id)
        
        st.metric(
            "Credits Remaining",
            credits_info['credits_remaining'],
            delta=f"-{credits_info['credits_used']} used"
        )
        
        st.caption(f"Total Credits: {credits_info['total_credits']}")
        st.caption(f"Used: {credits_info['credits_used']}")
    
    def get_modification_summary(self, trip_id, user_id):
        """Get a summary of modifications made to a trip"""
        modifications = db.get_trip_modifications(trip_id, user_id)
        chat_history = db.get_chat_history(trip_id, user_id)
        
        if not modifications and not chat_history:
            return "No modifications made yet."
        
        summary = f"Modification Summary:\n"
        summary += f"- {len(chat_history)} chat interactions\n"
        summary += f"- {len(modifications)} modifications applied\n"
        
        if modifications:
            summary += "\nRecent modifications:\n"
            for mod in modifications[-3:]:  # Show last 3 modifications
                summary += f"• {mod['modification_type']}: {mod['modification_reason']}\n"
        
        return summary
