"""Pub/Sub integration for observation/event processing."""

import json
from typing import Optional, Callable
from google.cloud import pubsub_v1
from google.api_core import retry
import os


class PubSubEventProcessor:
    """Pub/Sub-based event processor for observation flow."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID", "pulserelay-506715")
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        
        self.topic_path = self.publisher.topic_path(self.project_id, "pulse-observations")
        self.subscription_path = self.subscriber.subscription_path(self.project_id, "pulse-observations-sub")

    def publish_observation(self, session_id: str, text: str, extraction_result: dict) -> str:
        """Publish an observation event to Pub/Sub."""
        message = {
            "session_id": session_id,
            "text": text,
            "extraction_result": extraction_result,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
        
        future = self.publisher.publish(
            self.topic_path,
            json.dumps(message).encode("utf-8"),
            session_id=session_id,
        )
        return future.result()

    def subscribe_to_observations(self, callback: Callable) -> str:
        """Subscribe to observation events."""
        def message_callback(message):
            data = json.loads(message.data.decode("utf-8"))
            callback(data)
            message.ack()

        future = self.subscriber.subscribe(
            self.subscription_path,
            callback=message_callback,
        )
        return future

    def ensure_topic_exists(self):
        """Create the Pub/Sub topic if it doesn't exist."""
        try:
            self.publisher.create_topic(request={"name": self.topic_path})
            print(f"Created topic: {self.topic_path}")
        except Exception as e:
            if "ALREADY_EXISTS" in str(e):
                pass
            else:
                raise

    def ensure_subscription_exists(self):
        """Create the Pub/Sub subscription if it doesn't exist."""
        try:
            self.subscriber.create_subscription(
                request={
                    "name": self.subscription_path,
                    "topic": self.topic_path,
                    "ack_deadline_seconds": 60,
                }
            )
            print(f"Created subscription: {self.subscription_path}")
        except Exception as e:
            if "ALREADY_EXISTS" in str(e):
                pass
            else:
                raise
