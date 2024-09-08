## Travel Itinerary Chatbot with LLM and Langchain (POC)

This repository showcases a proof-of-concept (POC) chatbot leveraging large language models (LLMs) to create an interactive travel itinerary assistant. 

### Project Overview

Travel agencies often receive numerous customer inquiries regarding travel itineraries. Gathering basic information like destination, duration, number of travelers, and budget is currently a manual process requiring significant manpower. This POC aims to automate this data collection through an LLM-powered chatbot utilizing the Langchain framework. 

### Getting Started

This guide will help you set up the environment and run the chatbot application. Feel free to contribute and suggest improvements as we strive to enhance its capabilities further!

**Prerequisites:**

* Git
* Python 3
* Google Auth
* Flask
* Langchain

**Steps:**

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gargshailesh/travel-itinerary-chatbot.git
   ```

2. **Install dependencies:**

   ```bash
   cd travel-itinerary-chatbot
   pip install -r requirements.txt
   ```

3. **Set up Google Authentication:**

   * The UI utilizes Google Auth for security.
   * If you are new to Google Auth, Refer to the YouTube tutorial to configure Google Auth for Flask: https://www.youtube.com/watch?v=FKgJEfrhU1E
   * Download your Google credentials JSON file and rename it to `google_client_secret.json`.
   * Note down your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (needed for step 5).

4. **Configure Firestore Database:**

   * Create a Firebase account at [Link to Firebase Console].
   * Create a new Firebase project and note down the `Project ID` (required for environment variables in step 5).
   * Within your Firebase project, create a Firestore collection and note down its name (needed for environment variables).
   * Install the Google Cloud CLI following instructions here: [Link to Google Cloud CLI installation]
   * Authenticate the Google Cloud CLI with your Google account:
      - Run the following commands in your terminal:
         ```bash
         gcloud init
         gcloud auth application-default login
         ```
      - Follow steps outlined here to authenticate with your Google account: [Link to Google Cloud authentication]
   * Set your default project to the newly created Firebase project:
      ```bash
      gcloud config set project <Your GCP Project ID>
      ```
   * Enable the Firestore API in the Google Cloud Console:
      - Navigate to [Link to Google Cloud Console APIs]
      - Search for "Firestore API" and enable it for your project.

5. **Configure Environment Variables:**

   * Rename the `.env.example` file to `.env`.
   * Set the following environment variables within the `.env` file:
      - `GOOGLE_CLIENT_ID`: Your Google client ID from step 3d.
      - `GOOGLE_CLIENT_SECRET`: Your Google client secret from step 3d.
      - `REDIRECT_URI` : For localhost it should be something like "http://127.0.0.1:5000/callback"
      - `OPENAI_API_KEY` : Your openai api key
      - `PROJECT_ID`: Your Firebase project ID from step 4b.
      - `COLLECTION_NAME`: Your Firestore collection name from step 4c.

6. **Run the Flask App:**

   ```bash
   python travel_bot_app.py
   ```

This will launch the chatbot application. You can now access the chatbot and interact with it.
