"""
Beautiful Credit Widget for AI Trip Planner
Shows credit usage with modern UI components
"""

import streamlit as st
from datetime import datetime, timedelta
from database_config import get_database

class CreditWidget:
    """Beautiful credit display widget"""
    
    def __init__(self):
        pass
    
    def show_credit_card(self, user_id):
        """Show credit information in a beautiful card format"""
        try:
            db = get_database()
            credit_data = db.get_user_credits(user_id)
            
            if not credit_data:
                st.error("Unable to load credit information")
                return
            
            # Create a beautiful credit card
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin: 10px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            ">
                <h3 style="margin: 0 0 15px 0; color: white;">💳 AI Credits</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Credit metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="🎯 Credits Used",
                    value=credit_data['credits_used'],
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="💎 Credits Remaining",
                    value=credit_data['credits_remaining'],
                    delta=None
                )
            
            with col3:
                st.metric(
                    label="📊 Total Trips",
                    value=credit_data['total_trips'],
                    delta=None
                )
            
            # Progress bar
            progress = credit_data['credits_used'] / credit_data['total_credits']
            st.progress(progress)
            
            # Credit status
            if credit_data['credits_remaining'] > 500:
                st.success(f"✅ You have {credit_data['credits_remaining']} credits remaining!")
            elif credit_data['credits_remaining'] > 100:
                st.warning(f"⚠️ You have {credit_data['credits_remaining']} credits remaining. Consider upgrading!")
            else:
                st.error(f"🚨 Only {credit_data['credits_remaining']} credits left! Upgrade now!")
            
        except Exception as e:
            st.error(f"Error loading credit information: {str(e)}")
    
    def show_credit_sidebar(self, user_id):
        """Show compact credit info in sidebar"""
        try:
            # Debug: Check if user_id is valid
            if not user_id:
                st.sidebar.error("❌ No user ID provided")
                return
                
            db = get_database()
            credit_data = db.get_user_credits(user_id)
            
            if not credit_data:
                st.sidebar.error("❌ Unable to load credit data")
                return
            
            st.sidebar.markdown("### 💳 AI Credits")
            
            # Compact display
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                st.sidebar.metric(
                    label="Used",
                    value=credit_data['credits_used']
                )
            
            with col2:
                st.sidebar.metric(
                    label="Remaining",
                    value=credit_data['credits_remaining']
                )
            
            # Progress bar
            progress = credit_data['credits_used'] / credit_data['total_credits']
            st.sidebar.progress(progress)
            
            # Status indicator
            if credit_data['credits_remaining'] > 500:
                st.sidebar.success("✅ Credits available")
            elif credit_data['credits_remaining'] > 100:
                st.sidebar.warning("⚠️ Low credits")
            else:
                st.sidebar.error("🚨 Very low credits")
            
        except Exception as e:
            st.sidebar.error(f"Credit info unavailable: {str(e)}")
    
    def show_credit_history(self, user_id):
        """Show credit transaction history"""
        try:
            db = get_database()
            transactions = db.get_credit_transactions(user_id, limit=20)
            
            if not transactions:
                st.info("No credit transactions found.")
                return
            
            st.subheader("📋 Credit History")
            
            # Create a beautiful table
            for transaction in transactions:
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{transaction['description']}**")
                        if transaction['destination']:
                            st.caption(f"Trip: {transaction['destination']}")
                    
                    with col2:
                        if transaction['transaction_type'] == 'usage':
                            st.write(f"🔴 -{transaction['credits_amount']}")
                        else:
                            st.write(f"🟢 +{transaction['credits_amount']}")
                    
                    with col3:
                        st.write(transaction['transaction_type'].title())
                    
                    with col4:
                        st.write(transaction['created_at'][:10])
                    
                    st.divider()
            
        except Exception as e:
            st.error(f"Error loading credit history: {str(e)}")
    
    def show_credit_usage_breakdown(self, user_id):
        """Show credit usage breakdown by trip"""
        try:
            # Get trips with credit usage
            db = get_database()
            trips = db.get_user_trips(user_id)
            
            if not trips:
                st.info("No trips found.")
                return
            
            st.subheader("📊 Credit Usage by Trip")
            
            # Create a chart-like display
            total_credits = sum(trip.get('credits_used', 0) for trip in trips)
            
            if total_credits == 0:
                st.info("No credits used yet.")
                return
            
            for trip in trips:
                credits_used = trip.get('credits_used', 0)
                if credits_used > 0:
                    percentage = (credits_used / total_credits) * 100
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{trip['destination']}**")
                        st.caption(f"{trip['start_date']} to {trip['end_date']}")
                    
                    with col2:
                        st.write(f"{credits_used} credits")
                    
                    with col3:
                        st.write(f"{percentage:.1f}%")
                    
                    # Progress bar for this trip
                    st.progress(credits_used / 20)  # Assuming max 20 credits per trip
                    
                    st.divider()
            
        except Exception as e:
            st.error(f"Error loading credit breakdown: {str(e)}")
    
    def show_upgrade_prompt(self, user_id):
        """Show upgrade prompt when credits are low"""
        try:
            db = get_database()
            credit_data = db.get_user_credits(user_id)
            
            if not credit_data or credit_data['credits_remaining'] > 100:
                return
            
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin: 20px 0;
                text-align: center;
            ">
                <h3 style="margin: 0 0 10px 0;">🚨 Credits Running Low!</h3>
                <p style="margin: 0;">You have only {remaining} credits left. Upgrade now to continue planning amazing trips!</p>
            </div>
            """.format(remaining=credit_data['credits_remaining']), unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                if st.button("🚀 Upgrade Credits", type="primary", use_container_width=True):
                    st.info("Upgrade feature coming soon! Contact support for now.")
            
        except Exception as e:
            st.error(f"Error showing upgrade prompt: {str(e)}")

# Create global credit widget instance
credit_widget = CreditWidget()
