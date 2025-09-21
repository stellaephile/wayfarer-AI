"""
Credit Display Component for AI Trip Planner
Shows credit usage information to users
"""

import streamlit as st
from datetime import datetime, timedelta
from cloudsql_database_config import get_database
db = get_database()

class CreditDisplay:
    """Display credit usage information to users"""
    
    def __init__(self):
        pass
    
    def show_credit_summary(self, user_id):
        """Show credit summary in sidebar or main area"""
        try:
            credit_data = db.get_user_credit_summary(user_id)
            
            if not credit_data:
                st.warning("Unable to load credit information")
                return
            
            # Display total credits used
            total_credits = credit_data.get('total_credits_used', 0)
            last_updated = credit_data.get('last_updated')
            
            st.metric(
                label="💰 Total Credits Used",
                value=f"{total_credits:.2f}",
                help=f"Last updated: {last_updated if last_updated else 'Never'}"
            )
            
            # Show recent usage by type
            recent_usage = credit_data.get('recent_usage_by_type', [])
            if recent_usage:
                st.subheader("📊 Recent Usage (30 days)")
                for usage in recent_usage:
                    st.write(f"**{usage['type'].title()}:** {usage['total']:.2f} credits ({usage['count']} requests)")
            
            # Show usage by trip
            trip_usage = credit_data.get('usage_by_trip', [])
            if trip_usage:
                st.subheader("🗺️ Usage by Trip")
                for trip in trip_usage[:5]:  # Show top 5
                    st.write(f"**{trip['destination']}:** {trip['credits']:.2f} credits")
            
        except Exception as e:
            st.error(f"Error loading credit information: {str(e)}")
    
    def show_credit_analytics(self, user_id):
        """Show detailed credit analytics page"""
        st.title("💰 Credit Usage Analytics")
        
        try:
            credit_data = db.get_user_credit_summary(user_id)
            usage_history = db.get_credit_usage_history(user_id, limit=100)
            
            if not credit_data:
                st.warning("No credit data available")
                return
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Credits Used",
                    f"{credit_data.get('total_credits_used', 0):.2f}",
                    help="All-time credit usage"
                )
            
            with col2:
                recent_usage = credit_data.get('recent_usage_by_type', [])
                today_usage = sum([u['total'] for u in recent_usage if u['type'] == 'trip_generation'])
                st.metric(
                    "Today's Usage",
                    f"{today_usage:.2f}",
                    help="Credits used today"
                )
            
            with col3:
                trip_count = len(credit_data.get('usage_by_trip', []))
                st.metric(
                    "Trips Planned",
                    trip_count,
                    help="Number of trips with credit usage"
                )
            
            with col4:
                avg_per_trip = (credit_data.get('total_credits_used', 0) / max(trip_count, 1))
                st.metric(
                    "Avg per Trip",
                    f"{avg_per_trip:.2f}",
                    help="Average credits per trip"
                )
            
            # Usage by type chart
            st.subheader("📊 Usage by Type (Last 30 Days)")
            recent_usage = credit_data.get('recent_usage_by_type', [])
            
            if recent_usage:
                import pandas as pd
                
                df = pd.DataFrame(recent_usage)
                df['type'] = df['type'].str.title()
                
                st.bar_chart(df.set_index('type')['total'])
            else:
                st.info("No recent usage data available")
            
            # Usage history table
            st.subheader("📋 Recent Usage History")
            
            if usage_history:
                # Convert to DataFrame for better display
                df_history = pd.DataFrame(usage_history)
                df_history['created_at'] = pd.to_datetime(df_history['created_at'])
                df_history = df_history.sort_values('created_at', ascending=False)
                
                # Format the display
                display_df = df_history[['created_at', 'usage_type', 'credits_used', 'description', 'trip_destination']].copy()
                display_df.columns = ['Date', 'Type', 'Credits', 'Description', 'Trip']
                display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
                display_df['Credits'] = display_df['Credits'].round(2)
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("No usage history available")
            
            # Usage trends
            st.subheader("📈 Usage Trends")
            
            if usage_history:
                # Group by date
                df_history['date'] = df_history['created_at'].dt.date
                daily_usage = df_history.groupby('date')['credits_used'].sum().reset_index()
                daily_usage.columns = ['Date', 'Credits Used']
                
                st.line_chart(daily_usage.set_index('Date'))
            
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")
    
    def show_credit_breakdown(self, user_id, trip_id=None):
        """Show credit breakdown for a specific trip or general usage"""
        try:
            if trip_id:
                # Get usage for specific trip
                usage_history = db.get_credit_usage_history(user_id, limit=1000)
                trip_usage = [u for u in usage_history if u.get('trip_destination')]
                
                st.subheader(f"💰 Credit Breakdown for Trip")
                
                if trip_usage:
                    total_trip_credits = sum([u['credits_used'] for u in trip_usage])
                    st.metric("Total Trip Credits", f"{total_trip_credits:.2f}")
                    
                    # Show breakdown by type
                    type_breakdown = {}
                    for usage in trip_usage:
                        usage_type = usage['usage_type']
                        if usage_type not in type_breakdown:
                            type_breakdown[usage_type] = 0
                        type_breakdown[usage_type] += usage['credits_used']
                    
                    for usage_type, credits in type_breakdown.items():
                        st.write(f"**{usage_type.title()}:** {credits:.2f} credits")
                else:
                    st.info("No credit usage recorded for this trip")
            else:
                # General breakdown
                credit_data = db.get_user_credit_summary(user_id)
                recent_usage = credit_data.get('recent_usage_by_type', [])
                
                st.subheader("💰 Credit Breakdown")
                
                if recent_usage:
                    total_recent = sum([u['total'] for u in recent_usage])
                    
                    for usage in recent_usage:
                        percentage = (usage['total'] / total_recent * 100) if total_recent > 0 else 0
                        st.write(f"**{usage['type'].title()}:** {usage['total']:.2f} credits ({percentage:.1f}%)")
                else:
                    st.info("No recent usage data available")
                    
        except Exception as e:
            st.error(f"Error loading credit breakdown: {str(e)}")
    
    def show_credit_estimate(self, operation_type, estimated_size=0):
        """Show estimated credits for an operation"""
        try:
            from credit_calculator import CreditCalculator
            
            estimated_credits = CreditCalculator.estimate_credits_for_request(operation_type, estimated_size)
            
            st.info(f"💰 Estimated credits for {operation_type}: {estimated_credits:.2f}")
            
            # Show breakdown
            breakdown = CreditCalculator.get_credit_breakdown(operation_type, estimated_credits)
            
            with st.expander("Credit Breakdown Details"):
                st.json(breakdown)
                
        except Exception as e:
            st.warning(f"Could not estimate credits: {str(e)}")
    
    def show_admin_credit_summary(self):
        """Show credit summary for all users (admin function)"""
        st.title("👥 Admin - Credit Usage Summary")
        
        try:
            all_users_credits = db.get_all_users_credit_summary()
            
            if not all_users_credits:
                st.warning("No user credit data available")
                return
            
            # Convert to DataFrame for better display
            import pandas as pd
            
            df = pd.DataFrame(all_users_credits)
            df['total_credits_used'] = df['total_credits_used'].round(2)
            df['last_updated'] = pd.to_datetime(df['last_updated']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Sort by total credits used
            df = df.sort_values('total_credits_used', ascending=False)
            
            st.dataframe(df, use_container_width=True)
            
            # Summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_credits = df['total_credits_used'].sum()
                st.metric("Total Credits Used", f"{total_credits:.2f}")
            
            with col2:
                avg_credits = df['total_credits_used'].mean()
                st.metric("Average per User", f"{avg_credits:.2f}")
            
            with col3:
                active_users = len(df[df['total_credits_used'] > 0])
                st.metric("Active Users", active_users)
            
        except Exception as e:
            st.error(f"Error loading admin summary: {str(e)}")

# Usage example
if __name__ == "__main__":
    display = CreditDisplay()
    # This would be called from the main app with actual user_id
    # display.show_credit_analytics(user_id)
