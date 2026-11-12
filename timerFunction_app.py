import logging
import os
import subprocess
import tempfile
import azure.functions as func
from azure.cosmos import CosmosClient
from openai import AzureOpenAI

# ==========================================
# APP SETUP & ENVIRONMENT CONFIGURATION
# ==========================================
# Initialize the Azure Function app instance using the v2 programming model
app = func.FunctionApp()

# Retrieve necessary connection strings and endpoints securely from Azure App Settings
COSMOS_ENDPOINT = os.environ.get("COSMOS_ENDPOINT")
COSMOS_KEY = os.environ.get("COSMOS_KEY")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")

DATABASE_NAME = "cosmosdb-crowddetector"
CONTAINER_NAME = "cameras"
RESULTS_CONTAINER_NAME = "crowdReports"


# ==========================================
# PART 1: THE HOURLY TIMER TRIGGER
# ==========================================
# Uses a CRON expression ("0 0 * * * *") to automatically execute every hour on the hour.
@app.schedule(schedule="0 0 * * * *", arg_name="timer", run_on_startup=False, use_monitor=False)
def crowd_detector_timer(timer: func.TimerRequest) -> None:
    logging.info("Hourly holiday shopping crowd detector timer triggered.")

    try:
        # ==========================================
        # PART 2: CONNECT TO COSMOS DB & FETCH CAMERAS
        # ==========================================
        # Initialize the Cosmos DB client and query the container to retrieve 
        # all registered camera IDs and their live stream source URLs.
        client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
        database = client.get_database_client(DATABASE_NAME)
        cameras_container = database.get_container_client(CONTAINER_NAME)

        query = "SELECT c.id, c.name, c.streamUrl FROM c"
        cameras = list(cameras_container.query_items(query=query, enable_cross_partition_query=True))
        
        logging.info(f"Found {len(cameras)} cameras to process.")

        # Initialize Azure OpenAI client for vision classification
        openai_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        results_container = database.get_container_client(RESULTS_CONTAINER_NAME)

        for camera in cameras:
            camera_id = camera.get("id")
            stream_url = camera.get("streamUrl")
            logging.info(f"Processing camera {camera_id}: {stream_url}")
            
            # Create a safe temporary file path for the captured frame
            temp_frame_path = os.path.join(tempfile.gettempdir(), f"frame_{camera_id}.jpg")

            try:
                # ==========================================
                # PART 3: FRAME CAPTURE VIA FFMPEG
                # ==========================================
                # Uses a lightweight system subprocess to invoke ffmpeg, pulling 
                # a single snapshot frame (-vframes 1) from the live stream URL.
                ffmpeg_command = [
                    "ffmpeg",
                    "-y",                     # Overwrite temporary file if it exists
                    "-i", stream_url,         # Input stream URL (e.g., .m3u8 or rtsp)
                    "-vframes", "1",          # Capture exactly 1 frame
                    "-q:v", "2",              # High image quality output
                    temp_frame_path
                ]
                
                # Execute ffmpeg command with a timeout to prevent hanging on dead streams
                subprocess.run(ffmpeg_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=True)

                if not os.path.exists(temp_frame_path):
                    logging.warning(f"FFmpeg failed to generate frame for camera {camera_id}")
                    continue

                # ==========================================
                # PART 4: CLASSIFICATION VIA AZURE OPENAI
                # ==========================================
                # Reads the captured image, encodes it, and sends it to GPT-4o 
                # to classify the visual crowd density as small, medium, or large.
                import base64
                with open(temp_frame_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

                response = openai_client.chat.completions.create(
                    model="gpt-4o",  # Deployment name of your vision model
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a retail crowd analysis expert. Analyze the provided image and classify the crowd density strictly into one of three words: 'small', 'medium', or 'large'."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Classify the crowd density in this storefront/street frame as small, medium, or large."},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                            ]
                        }
                    ],
                    max_tokens=10
                )

                classification = response.choices[0].message.content.strip().lower()
                logging.info(f"Camera {camera_id} crowd classification: {classification}")

                # ==========================================
                # PART 5: WRITE TO COSMOS DB & CLEANUP
                # ==========================================
                # Construct the result record, write/upsert it back into Cosmos DB, 
                # and securely delete the local temporary image file to avoid disk bloat.
                from datetime import datetime, timezone
                report_doc = {
                    "id": f"{camera_id}-{int(datetime.now(timezone.utc).timestamp())}",
                    "cameraId": camera_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "crowdLevel": classification
                }

                results_container.upsert_item(report_doc)
                logging.info(f"Successfully saved report for camera {camera_id} to Cosmos DB.")

            except Exception as cam_error:
                logging.error(f"Error processing individual camera {camera_id}: {str(cam_error)}")

            finally:
                # Cleanup: Ensure the local temporary frame is deleted even if errors occur
                if os.path.exists(temp_frame_path):
                    os.remove(temp_frame_path)

    except Exception as e:
        logging.error(f"Error running crowd detector pipeline: {str(e)}")