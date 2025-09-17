import json
import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import logging
import os


logging.basicConfig(
    filename=os.getenv("DATABASE_LOG"),
    level=logging.ERROR,  # can use INFO or DEBUG if you want more verbosity
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class FirestoreDatabaseManager:
    def __init__(self):
        firebase_config_path = os.getenv("FIREBASE_CONFIG")
        if not firebase_config_path:
            raise ValueError("FIREBASE_CONFIG not set in .env")

        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()

    # ---------------- USERS ----------------
    def create_user(self, username, email, password, name=None):
        try:
            password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user_ref = self.db.collection("users").document()
            user_ref.set({
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "name": name,
                "google_id": None,
                "picture": None,
                "verified_email": False,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": None,
                "is_active": True,
                "login_method": "email",
                "personal_number": None,
                "address": None,
                "pincode": None,
                "state": None,
                "alternate_number": None
            })
            return True, f"User created successfully with ID: {user_ref.id}"
        except Exception as e:
            return False, f"Error creating user: {str(e)}"

    def create_google_user(self, username, email, name, google_id, picture="", verified_email=False):
        try:
            user_ref = self.db.collection("users").document()
            user_ref.set({
                "username": username,
                "email": email,
                "password_hash": None,
                "name": name,
                "google_id": google_id,
                "picture": picture,
                "verified_email": verified_email,
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_login": None,
                "is_active": True,
                "login_method": "google"
            })
            return True, f"Google user created successfully with ID: {user_ref.id}"
        except Exception as e:
            return False, f"Error creating Google user: {str(e)}"

    def authenticate_user(self, username_or_email, password):
        try:
            query = self.db.collection("users").where("is_active", "==", True)
            if "@" in username_or_email:
                query = query.where("email", "==", username_or_email)
            else:
                query = query.where("username", "==", username_or_email)

            docs = list(query.stream())
            if not docs:
                return None

            user = docs[0].to_dict()
            user["id"] = docs[0].id

            if user.get("password_hash") and bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
                self.update_last_login(user["id"])
                return user
            return None
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

    def get_user_by_id(self, user_id):
        doc = self.db.collection("users").document(user_id).get()
        if doc.exists:
            user = doc.to_dict()
            user["id"] = doc.id
            return user
        return None

    def get_user_by_email(self, email):
        docs = list(self.db.collection("users").where("email", "==", email).where("is_active", "==", True).stream())
        if docs:
            user = docs[0].to_dict()
            user["id"] = docs[0].id
            return user
        return None

    def update_user_profile(self, user_id, **kwargs):
        try:
            allowed_fields = ["name", "personal_number", "address", "pincode", "state", "alternate_number"]
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            if not update_data:
                return False, "No valid fields to update"
            self.db.collection("users").document(user_id).update(update_data)
            return True, "Profile updated successfully"
        except Exception as e:
            return False, f"Error updating profile: {str(e)}"

    def update_last_login(self, user_id):
        self.db.collection("users").document(user_id).update({
            "last_login": firestore.SERVER_TIMESTAMP
        })

    # ---------------- TRIPS ----------------
    def create_trip(self, user_id, destination, start_date, end_date, budget, preferences, ai_suggestions, currency="USD", currency_symbol="$"):
        try:
            user_ref = self.db.collection("users").document(str(user_id))  # ensure str
            trip_ref = user_ref.collection("trips")

            # Create a new document with auto-generated ID
            trip_doc = trip_ref.document()  
            trip_doc.set({
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "preferences": preferences,
                "ai_suggestions": ai_suggestions,
                "currency": currency,
                "currency_symbol": currency_symbol,
                "status": "planned",
                "booking_status": "not_booked",
                "booking_id": None,
                "booking_confirmation": None,
                "credits_used": 0,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            return True, trip_doc.id   # 🔑 Return actual trip_id string
        except Exception as e:
            logger.error(f"❌ Error creating trip for user={user_id}: {str(e)}", exc_info=True)
            return False, str(e)

    def get_user_trips(self, user_id):
        try:
            trips_ref = self.db.collection("users").document(user_id).collection("trips")
            docs = trips_ref.order_by("created_at", direction=firestore.Query.DESCENDING).stream()
            return [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e:
            print(f"Error getting trips: {str(e)}")
            return []

    def get_trip_by_id(self, trip_id, user_id):
        doc = self.db.collection("users").document(user_id).collection("trips").document(trip_id).get()
        if doc.exists:
            trip = doc.to_dict()
            trip["id"] = doc.id
            return trip
        return None

    def update_trip(self, trip_id, user_id, **kwargs):
        try:
            kwargs["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("users").document(user_id).collection("trips").document(trip_id).update(kwargs)
            return True, "Trip updated successfully"
        except Exception as e:
            return False, f"Error updating trip: {str(e)}"

    def delete_trip(self, trip_id, user_id):
        try:
            self.db.collection("users").document(user_id).collection("trips").document(trip_id).delete()
            return True, "Trip deleted successfully"
        except Exception as e:
            return False, f"Error deleting trip: {str(e)}"

    # ---------------- CREDITS ----------------
    def get_user_credits(self, user_id):
        try:
            trips_ref = self.db.collection("users").document(user_id).collection("trips").stream()
            total_used = sum([trip.to_dict().get("credits_used", 0) for trip in trips_ref])
            total_credits = 1000
            return {
                "total_credits": total_credits,
                "credits_used": total_used,
                "credits_remaining": total_credits - total_used
            }
        except Exception as e:
            print(f"Error getting credits: {str(e)}")
            return {"total_credits": 1000, "credits_used": 0, "credits_remaining": 1000}

    def add_credit_transaction(self, user_id, trip_id, transaction_type, credits_amount, description):
        try:
            txn_ref = self.db.collection("users").document(user_id).collection("credit_transactions").document()
            txn_ref.set({
                "trip_id": trip_id,
                "transaction_type": transaction_type,
                "credits_amount": credits_amount,
                "description": description,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error adding credit transaction: {str(e)}")
            return False

    def get_credit_transactions(self, user_id, limit=10):
        try:
            docs = self.db.collection("users").document(user_id).collection("credit_transactions").order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
            return [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e:
            print(f"Error getting credit transactions: {str(e)}")
            return []

    # ---------------- CHAT ----------------
    def save_chat_interaction(self, trip_id, user_id, message_type, message_content, ai_response=None, credits_used=0):
        try:
            chat_ref = self.db.collection("users").document(user_id).collection("trips").document(trip_id).collection("chat_history").document()
            chat_ref.set({
                "message_type": message_type,
                "message_content": message_content,
                "ai_response": ai_response,
                "credits_used": credits_used,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error saving chat: {str(e)}")
            return False

    def get_chat_history(self, trip_id, user_id):
        try:
            docs = self.db.collection("users").document(user_id).collection("trips").document(trip_id).collection("chat_history").order_by("created_at").stream()
            return [doc.to_dict() | {"id": doc.id} for doc in docs]
        except Exception as e:
            print(f"Error getting chat history: {str(e)}")
            return []

    # ---------------- TRIP MODIFICATIONS ----------------
    def save_trip_modification(self, trip_id, user_id, modification_type, original_data, modified_data, modification_reason, credits_used=0):
        try:
            mod_ref = self.db.collection("users").document(user_id).collection("trips").document(trip_id).collection("modifications").document()
            mod_ref.set({
                "modification_type": modification_type,
                "original_data": json.dumps(original_data),
                "modified_data": json.dumps(modified_data),
                "modification_reason": modification_reason,
                "credits_used": credits_used,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error saving modification: {str(e)}")
            return False

    def get_trip_modifications(self, trip_id, user_id):
        try:
            docs = self.db.collection("users").document(user_id).collection("trips").document(trip_id).collection("modifications").order_by("created_at").stream()
            return [
                {
                    "id": doc.id,
                    **doc.to_dict(),
                    "original_data": json.loads(doc.to_dict().get("original_data", "{}")),
                    "modified_data": json.loads(doc.to_dict().get("modified_data", "{}"))
                }
                for doc in docs
            ]
        except Exception as e:
            print(f"Error getting modifications: {str(e)}")
            return []
    
    def update_trip_credits(self, user_id: str, trip_id: str, credits_used: int):
        try:
            trip_ref = (
                self.db.collection("users")
                .document(str(user_id))
                .collection("trips")
                .document(str(trip_id))
            )
            trip_ref.update({
                "credits_used": firestore.Increment(credits_used),
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            logger.info(
                f"✅ Updated credits for trip_id={trip_id}, user_id={user_id}, credits_used={credits_used}"
            )
            return True
        except Exception as e:
            logger.error(
                f"❌ Failed to update credits for trip_id={trip_id}, user_id={user_id}: {str(e)}",
                exc_info=True
            )
            return False



# Global instance
db = FirestoreDatabaseManager()
