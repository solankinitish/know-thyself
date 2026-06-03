from app.tracks.fitness_track import FitnessTrack
from app.tracks.habits_track import HabitsTrack
from app.tracks.relationships_track import RelationshipsTrack
from app.utils.logger import get_logger
from app.utils.config import settings
import pandas as pd


class CoachingService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.track_map = {
            "fitness": FitnessTrack,
            "habits": HabitsTrack,
            "relationships": RelationshipsTrack
        }
        self.active_coaches = {}
    
    def get_coach(self, user_id, track):
        if not user_id:
            raise ValueError("user_id is blank.")
        if track not in self.track_map:
            raise ValueError("Track not in Track Map.")
        # On first message
        key = f"{user_id}_{track}"
        if key not in self.active_coaches:
            track_class = self.track_map[track]
            self.active_coaches[key] = track_class(user_id=user_id)
        self.logger.info(f"Coach created for {user_id} on {track} track.")
        return self.active_coaches[key]

    def chat(self, user_id, track, message):
        if not message or not message.strip():
            raise ValueError("Message cannot be empty.")
        coach = self.get_coach(user_id, track)
        self.logger.info(f"Chat request from {user_id} on {track} track.")
        return coach.respond(message)

    def log_fitness(self, user_id, data):
        if not user_id:
            raise ValueError("user_id is blank.")
        if not data:
            raise ValueError("Data is empty.")
        
        gcs_path = f"gs://{settings.gcs_bucket}/fitness/{user_id}.csv"

        try:
            existing_df = pd.read_csv(gcs_path)
            df = pd.concat([existing_df, pd.DataFrame([data])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([data])
        
        df.to_csv(gcs_path, index=False)
        self.logger.info(f"Data logged for {user_id}.")

    def log_habits(self, user_id, data):
        if not user_id:
            raise ValueError("user_id is blank.")
        if not data:
            raise ValueError("Data is empty.")
        
        gcs_path = f"gs://{settings.gcs_bucket}/habits/{user_id}.csv"

        try:
            existing_df = pd.read_csv(gcs_path)
            df = pd.concat([existing_df, pd.DataFrame([data])], ignore_index=True)
        except FileNotFoundError:
            df = pd.DataFrame([data])
        
        df.to_csv(gcs_path, index=False)
        self.logger.info(f"Data logged for {user_id}.")
