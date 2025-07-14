Here is the documentation that needs to be follow in the project agent_neo4j. 
Deploy to Vertex AI Agent Engine¶
python_only

Agent Engine is a fully managed Google Cloud service enabling developers to deploy, manage, and scale AI agents in production. Agent Engine handles the infrastructure to scale agents in production so you can focus on creating intelligent and impactful applications.


from vertexai import agent_engines

remote_app = agent_engines.create(
    agent_engine=root_agent,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]",
    ]
)
Install Vertex AI SDK¶
Agent Engine is part of the Vertex AI SDK for Python. For more information, you can review the Agent Engine quickstart documentation.

Install the Vertex AI SDK¶

pip install google-cloud-aiplatform[adk,agent_engines]
Info

Agent Engine only supported Python version >=3.9 and <=3.12.

Initialization¶

import vertexai

PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://your-google-cloud-storage-bucket"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)
For LOCATION, you can check out the list of supported regions in Agent Engine.

Create your agent¶
You can use the sample agent below, which has two tools (to get weather or retrieve the time in a specified city):


import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


root_agent = Agent(
    name="weather_time_agent",
    model="gemini-2.0-flash",
    description=(
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],
)
Prepare your agent for Agent Engine¶
Use reasoning_engines.AdkApp() to wrap your agent to make it deployable to Agent Engine


from vertexai.preview import reasoning_engines

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)
Try your agent locally¶
You can try it locally before deploying to Agent Engine.

Create session (local)¶

session = app.create_session(user_id="u_123")
session
Expected output for create_session (local):


Session(id='c6a33dae-26ef-410c-9135-b434a528291f', app_name='default-app-name', user_id='u_123', state={}, events=[], last_update_time=1743440392.8689594)
List sessions (local)¶

app.list_sessions(user_id="u_123")
Expected output for list_sessions (local):


ListSessionsResponse(session_ids=['c6a33dae-26ef-410c-9135-b434a528291f'])
Get a specific session (local)¶

session = app.get_session(user_id="u_123", session_id=session.id)
session
Expected output for get_session (local):


Session(id='c6a33dae-26ef-410c-9135-b434a528291f', app_name='default-app-name', user_id='u_123', state={}, events=[], last_update_time=1743681991.95696)
Send queries to your agent (local)¶

for event in app.stream_query(
    user_id="u_123",
    session_id=session.id,
    message="whats the weather in new york",
):
print(event)
Expected output for stream_query (local):


{'parts': [{'function_call': {'id': 'af-a33fedb0-29e6-4d0c-9eb3-00c402969395', 'args': {'city': 'new york'}, 'name': 'get_weather'}}], 'role': 'model'}
{'parts': [{'function_response': {'id': 'af-a33fedb0-29e6-4d0c-9eb3-00c402969395', 'name': 'get_weather', 'response': {'status': 'success', 'report': 'The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit).'}}}], 'role': 'user'}
{'parts': [{'text': 'The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit).'}], 'role': 'model'}
Deploy your agent to Agent Engine¶

from vertexai import agent_engines

remote_app = agent_engines.create(
    agent_engine=root_agent,
    requirements=[
        "google-cloud-aiplatform[adk,agent_engines]"   
    ]
)
This step may take several minutes to finish. Each deployed agent has a unique identifier. You can run the following command to get the resource_name identifier for your deployed agent:


remote_app.resource_name
The response should look like the following string:


f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}"
For additional details, you can visit the Agent Engine documentation deploying an agent and managing deployed agents.

Try your agent on Agent Engine¶
Create session (remote)¶

remote_session = remote_app.create_session(user_id="u_456")
remote_session
Expected output for create_session (remote):


{'events': [],
'user_id': 'u_456',
'state': {},
'id': '7543472750996750336',
'app_name': '7917477678498709504',
'last_update_time': 1743683353.030133}
id is the session ID, and app_name is the resource ID of the deployed agent on Agent Engine.

List sessions (remote)¶

remote_app.list_sessions(user_id="u_456")
Get a specific session (remote)¶

remote_app.get_session(user_id="u_456", session_id=remote_session["id"])
Note

While using your agent locally, session ID is stored in session.id, when using your agent remotely on Agent Engine, session ID is stored in remote_session["id"].

Send queries to your agent (remote)¶

for event in remote_app.stream_query(
    user_id="u_456",
    session_id=remote_session["id"],
    message="whats the weather in new york",
):
    print(event)
Expected output for stream_query (remote):


{'parts': [{'function_call': {'id': 'af-f1906423-a531-4ecf-a1ef-723b05e85321', 'args': {'city': 'new york'}, 'name': 'get_weather'}}], 'role': 'model'}
{'parts': [{'function_response': {'id': 'af-f1906423-a531-4ecf-a1ef-723b05e85321', 'name': 'get_weather', 'response': {'status': 'success', 'report': 'The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit).'}}}], 'role': 'user'}
{'parts': [{'text': 'The weather in New York is sunny with a temperature of 25 degrees Celsius (41 degrees Fahrenheit).'}], 'role': 'model'}
Clean up¶
After you have finished, it is a good practice to clean up your cloud resources. You can delete the deployed Agent Engine instance to avoid any unexpected charges on your Google Cloud account.


remote_app.delete(force=True)
force=True will also delete any child resources that were generated from the deployed agent, such as sessions.
Using memory in Google ADK
Using state in Google ADK
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.genai.types import Content, Part

# Define agent with output_key
greeting_agent = LlmAgent(
    name="Greeter",
    model="gemini-2.0-flash", # Use a valid model
    instruction="Generate a short, friendly greeting.",
    output_key="last_greeting" # Save response to state['last_greeting']
)

# --- Setup Runner and Session ---
app_name, user_id, session_id = "state_app", "user1", "session1"
session_service = InMemorySessionService()
runner = Runner(
    agent=greeting_agent,
    app_name=app_name,
    session_service=session_service
)
session = await session_service.create_session(app_name=app_name,
                                    user_id=user_id,
                                    session_id=session_id)
print(f"Initial state: {session.state}")

# --- Run the Agent ---
# Runner handles calling append_event, which uses the output_key
# to automatically create the state_delta.
user_message = Content(parts=[Part(text="Hello")])
for event in runner.run(user_id=user_id,
                        session_id=session_id,
                        new_message=user_message):
    if event.is_final_response():
      print(f"Agent responded.") # Response text is also in event.content

# --- Check Updated State ---
updated_session = await session_service.get_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
print(f"State after agent run: {updated_session.state}")
# Expected output might include: {'last_greeting': 'Hello there! How can I help you today?'}


How ot use callback in adk 
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.runners import Runner
from typing import Optional
from google.genai import types 
from google.adk.sessions import InMemorySessionService

GEMINI_2_FLASH="gemini-2.0-flash"

# --- Define the Callback Function ---
def simple_before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}")

    # Inspect the last user message in the request contents
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
         if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    print(f"[Callback] Inspecting last user message: '{last_user_message}'")

    # --- Modification Example ---
    # Add a prefix to the system instruction
    original_instruction = llm_request.config.system_instruction or types.Content(role="system", parts=[])
    prefix = "[Modified by Callback] "
    # Ensure system_instruction is Content and parts list exists
    if not isinstance(original_instruction, types.Content):
         # Handle case where it might be a string (though config expects Content)
         original_instruction = types.Content(role="system", parts=[types.Part(text=str(original_instruction))])
    if not original_instruction.parts:
        original_instruction.parts.append(types.Part(text="")) # Add an empty part if none exist

    # Modify the text of the first part
    modified_text = prefix + (original_instruction.parts[0].text or "")
    original_instruction.parts[0].text = modified_text
    llm_request.config.system_instruction = original_instruction
    print(f"[Callback] Modified system instruction to: '{modified_text}'")

    # --- Skip Example ---
    # Check if the last user message contains "BLOCK"
    if "BLOCK" in last_user_message.upper():
        print("[Callback] 'BLOCK' keyword found. Skipping LLM call.")
        # Return an LlmResponse to skip the actual LLM call
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="LLM call was blocked by before_model_callback.")],
            )
        )
    else:
        print("[Callback] Proceeding with LLM call.")
        # Return None to allow the (modified) request to go to the LLM
        return None


# Create LlmAgent and Assign Callback
my_llm_agent = LlmAgent(
        name="ModelCallbackAgent",
        model=GEMINI_2_FLASH,
        instruction="You are a helpful assistant.", # Base instruction
        description="An LLM agent demonstrating before_model_callback",
        before_model_callback=simple_before_model_modifier # Assign the function here
)

APP_NAME = "guardrail_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=my_llm_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("write a joke on BLOCK")

for sesssion handling in Google ADK look at this url https://google.github.io/adk-docs/sessions/session/#the-session-object

Deployment look at this url https://google.github.io/adk-docs/deploy/agent-engine/
def deploy_neo4j_agent():
    """Deploy the Neo4j agent to Vertex AI Agent Engine."""
    try:
        print("\n📦 Step 1: Wrapping agent in deployable ADK App...")
        deployable_app = reasoning_engines.AdkApp(agent=neo4j_agent, enable_tracing=True)
        print("✅ Agent wrapped successfully.")

        print("\n🧪 Step 2: Running final local test...")
        test_events = list(deployable_app.stream_query(
            user_id="deployment_test_user",
            message="Test connection to database",
        ))
        print(f"✅ Final test completed ({len(test_events)} events).")

        print("\n☁️ Step 3: Deploying to Vertex AI Agent Engine...")
        print("   📤 Uploading code and dependencies...")
        print("   🔧 Creating agent service...")
        print("   ⚙️  Configuring environment...")

        # Deploy to Agent Engine
        remote_agent = agent_engines.create(
            deployable_app,
            display_name=AGENT_DISPLAY_NAME,
            description=deployment_description,
            requirements=deployment_requirements,
            env_vars=deployment_env_vars
        )

        print("\n🎉 DEPLOYMENT SUCCESSFUL! 🎉")
        print("\n📋 Deployment Details:")
        print(f"   🤖 Agent Name: {AGENT_DISPLAY_NAME}")
        print(f"   🆔 Resource ID: {remote_agent.resource_name}")
        print(f"   🌍 Region: {LOCATION}")
        print(f"   📊 Model: {MODEL_NAME}")

        print("\n🔗 Access Your Agent:")
        print(f"   📱 Google Cloud Console: https://console.cloud.google.com/vertex-ai?project={PROJECT_ID}")
        print("   🔍 Navigate to: Vertex AI → Agent Builder → Your Agent")

        rint("🧪 Testing deployed agent...")

# Get the deployed agent resource name
if 'deployed_agent' in locals() and deployed_agent:
    agent_resource_name = deployed_agent.resource_name
    print(f"   🆔 Agent Resource: {agent_resource_name}")
else:
    print("❌ No deployed agent found. Please run the deployment step first.")
    print("   If you have a previously deployed agent, enter its resource name below:")
    # You can manually set the resource name here if needed
    # agent_resource_name = "projects/YOUR_PROJECT/locations/YOUR_REGION/reasoningEngines/YOUR_ID"
    raise SystemExit("Deployed agent not found.")

try:
    print("\n🔗 Connecting to deployed agent...")
    remote_agent = agent_engines.get(agent_resource_name)
    print("✅ Connected successfully!")

    # Test with a comprehensive query
    test_questions = [
        "Show me a summary of what data is in this database",
        "List all the types of nodes in the database",
        "Give me a sample of data from the most interesting node type"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 60)

        try:
            # Stream the response
            response_received = False
            for event in remote_agent.stream_query(
                user_id=f"test_user_{i}",
                message=question,
            ):
                # Check for text responses
                if ('content' in event and
                    'parts' in event['content'] and
                    event['content']['parts']):

                    for part in event['content']['parts']:
                        if 'text' in part:
                            print(part['text'])
                            response_received = True
                        elif 'function_call' in part:
                            function_name = part['function_call']['name']
                            print(f"🔧 Calling: {function_name}")

            if response_received:
                print(f"\n✅ Test {i} completed successfully!")
            else:
                print(f"\n⚠️  Test {i} completed but no text response received.")

        except Exception as e:
            print(f"\n❌ Test {i} failed: {e}")

    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT AND TESTING COMPLETE! 🎉")
    print("\n✅ Your Neo4j AI Agent is now live and functional!")

    print("\n📋 Summary:")
    print(f"   🤖 Agent Name: {AGENT_DISPLAY_NAME}")
    print(f"   🆔 Resource ID: {agent_resource_name}")
    print(f"   🗄️  Database: Connected to Neo4j")
    print(f"   🧠 Model: {MODEL_NAME}")
    print(f"   🌍 Region: {LOCATION}")

    print("\n🚀 Next Steps:")
    print("   1. Share the Google Cloud Console link with your team")
    print("   2. Test with your own questions via the console")
    print("   3. Integrate via API if needed")
    print("   4. Monitor usage and performance")

    print("\n🔗 Quick Access:")
    print(f"   📱 Console: https://console.cloud.google.com/vertex-ai?project={PROJECT_ID}")
    print("   📖 Documentation: https://cloud.google.com/vertex-ai/docs")

except Exception as e:
    print(f"\n❌ Testing failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("   1. Wait a few minutes for deployment to fully complete")
    print("   2. Check the Google Cloud Console for any errors")
    print("   3. Verify your Neo4j database is still accessible")
    print("   4. Check agent logs in Google Cloud Logging")

 Get the deployed agent resource name
if 'deployed_agent' in locals() and deployed_agent:
    agent_resource_name = deployed_agent.resource_name
    print(f"   🆔 Agent Resource: {agent_resource_name}")
else:
    print("❌ No deployed agent found. Please run the deployment step first.")
    print("   If you have a previously deployed agent, enter its resource name below:")
    # You can manually set the resource name here if needed
    # agent_resource_name = "projects/YOUR_PROJECT/locations/YOUR_REGION/reasoningEngines/YOUR_ID"
    raise SystemExit("Deployed agent not found.")

try:
    print("\n🔗 Connecting to deployed agent...")
    remote_agent = agent_engines.get(agent_resource_name)
    print("✅ Connected successfully!")

    # Test with a comprehensive query
    test_questions = [
        "Show me a summary of what data is in this database",
        "List all the types of nodes in the database",
        "Give me a sample of data from the most interesting node type"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n📝 Test {i}: {question}")
        print("-" * 60)

        try:
            # Stream the response
            response_received = False
            for event in remote_agent.stream_query(
                user_id=f"test_user_{i}",
                message=question,
            ):
                # Check for text responses
                if ('content' in event and
                    'parts' in event['content'] and
                    event['content']['parts']):

                    for part in event['content']['parts']:
                        if 'text' in part:
                            print(part['text'])
                            response_received = True
                        elif 'function_call' in part:
                            function_name = part['function_call']['name']
                            print(f"🔧 Calling: {function_name}")

            if response_received:
                print(f"\n✅ Test {i} completed successfully!")
            else:
                print(f"\n⚠️  Test {i} completed but no text response received.")

        except Exception as e:
            print(f"\n❌ Test {i} failed: {e}")

    print("\n" + "=" * 60)
    print("🎉 DEPLOYMENT AND TESTING COMPLETE! 🎉")
    print("\n✅ Your Neo4j AI Agent is now live and functional!")

    print("\n📋 Summary:")
    print(f"   🤖 Agent Name: {AGENT_DISPLAY_NAME}")
    print(f"   🆔 Resource ID: {agent_resource_name}")
    print(f"   🗄️  Database: Connected to Neo4j")
    print(f"   🧠 Model: {MODEL_NAME}")
    print(f"   🌍 Region: {LOCATION}")

Replace PASTE_YOUR_US_CENTRAL1_AGENT_RESOURCE_NAME_HERE with the full resource name of your newly deployed agent.
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://discoveryengine.googleapis.com/v1alpha/projects/test-disco-cm/locations/global/collections/default_collection/engines/globalagentspacetest_1750867794660/assistants/default_assistant/agents" \
-d '{
  "displayName": "Financial Advisor Agent (US-Central1 Test)",
  "description": "An agent for providing financial advice and market analysis.",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "Use this tool when you need to answer questions about finance, stock prices, exchange rates, or market trends. It can provide financial advice and analysis."
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "PASTE_YOUR_US_CENTRAL1_AGENT_RESOURCE_NAME_HERE"
    }
  }
}'

Overview over all agents registered to agentspace
pilotagentspace_1746265175097 application.

This command uses the eu regional endpoint since that's where your app is located.
curl -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://eu-discoveryengine.googleapis.com/v1alpha/projects/test-disco-cm/locations/eu/collections/default_collection/engines/pilotagentspace_1746265175097/assistants/default_assistant/agents"
The Correct Delete Command Please run this single, complete command. I have constructed the full URL using the agent name from your output. This will work.
curl -X DELETE \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://discoveryengine.googleapis.com/v1alpha/projects/881765721010/locations/global/collections/default_collection/engines/globalagentspacetest_1750867794660/assistants/default_assistant/agents/13873616461497971196"

or
# Get the latest agent ID first
# You can run the GET command to find the latest agent ID if you don't have it
LATEST_AGENT_ID="PASTE_LATEST_AGENT_ID_HERE"

curl -X DELETE \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://eu-discoveryengine.googleapis.com/v1alpha/projects/881765721010/locations/eu/collections/default_collection/engines/pilotagentspace_1746265175097/assistants/default_assistant/agents/${LATEST_AGENT_ID}"

Searching for Authorization Resources - when setting up with Authorization
curl -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://discoveryengine.googleapis.com/v1alpha/projects/test-disco-cm/locations/global/authorizations"

If noen found, Create an Authoristion Resource:

# This command creates the OAuth resource in the correct GLOBAL endpoint
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://discoveryengine.googleapis.com/v1alpha/projects/test-disco-cm/locations/global/authorizations?authorizationId=financial-advisor-auth" \
-d '{
  "name": "projects/test-disco-cm/locations/global/authorizations/financial-advisor-auth",
  "serverSideOauth2": {
    "clientId": "YOUR_CLIENT_ID_HERE",
    "clientSecret": "YOUR_CLIENT_SECRET_HERE",
    "authorizationUri": "https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID_HERE&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email&response_type=code&access_type=offline&prompt=consent",
    "tokenUri": "https://oauth2.googleapis.com/token"
  }
}'

 Get the Latest Agent's Full Resource Name Look through the list and find the name of the "Financial Advisor Agent" with the most recent createTime.
 url -X GET \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://eu-discoveryengine.googleapis.com/v1alpha/projects/881765721010/locations/eu/collections/default_collection/engines/pilotagentspace_1746265175097/assistants/default_assistant/agents"

Step 2: Adding an Agent Authorization

Finally, we create the agent in the eu endpoint and give it the full path to the global resource you just made.
curl -X POST \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://eu-discoveryengine.googleapis.com/v1alpha/projects/881765721010/locations/eu/collections/default_collection/engines/pilotagentspace_1746265175097/assistants/default_assistant/agents" \
-d '{
  "displayName": "Financial Advisor Agent",
  "description": "An agent for providing financial advice and market analysis.",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "Use this tool when you need to answer questions about finance, stock prices, exchange rates, or market trends. It can provide financial advice and analysis."
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "projects/881765721010/locations/eu/reasoningEngines/1074952936057995264"
    },
    "authorizations": [
      "projects/test-disco-cm/locations/global/authorizations/financial-advisor-auth"
    ]
  }
}'
Patching an Agent with Authorization.italicized text Take the full name you just copied and use it to replace PASTE_THE_LATEST_AGENT_NAME_HERE in the command below. This script will update that agent to require the global authorization resource.
# Replace the placeholder with the full agent "name" from Step 1
AGENT_RESOURCE_NAME="PASTE_THE_LATEST_AGENT_NAME_HERE"

curl -X PATCH \
-H "Authorization: Bearer $(gcloud auth print-access-token)" \
-H "Content-Type: application/json" \
-H "X-Goog-User-Project: test-disco-cm" \
"https://eu-discoveryengine.googleapis.com/v1alpha/${AGENT_RESOURCE_NAME}" \
-d '{
  "displayName": "Financial Advisor Agent",
  "description": "An agent for providing financial advice and market analysis.",
  "adk_agent_definition": {
    "tool_settings": {
      "tool_description": "Use this tool when you need to answer questions about finance, stock prices, exchange rates, or market trends. It can provide financial advice and analysis."
    },
    "provisioned_reasoning_engine": {
      "reasoning_engine": "projects/881765721010/locations/global/reasoningEngines/1074952936057995264"
    },
    "authorizations": [
      "projects/881765721010/locations/global/authorizations/financial-advisor-auth"
    ]
  }
}'

Deploy an agent

bookmark_border
To deploy an agent on Vertex AI Agent Engine, use the following steps:

Configure your agent for deployment.
Create an AgentEngine instance.
Grant the deployed agent permissions.
Get the agent resource ID.
You can also use Agent Starter Pack templates for deployment.

Note: Vertex AI Agent Engine deployment only supports Python.
Before you begin
Before you deploy an agent, make sure you have completed the following tasks:

Set up your environment.
Develop an agent.
Configure your agent for deployment
You can make the following optional configurations:

Package requirements
Additional packages
Environment variables
Build options
Cloud Storage folder
Resource metadata
Define the package requirements
Provide the set of packages required by the agent for deployment. The set of packages can either be a list of items to be installed by pip, or the path to a file that follows the Requirements File Format. Use the following best practices:

Pin your package versions for reproducible builds. Common packages to keep track of include the following: google-cloud-aiplatform, cloudpickle, langchain, langchain-core, langchain-google-vertexai, and pydantic.

Minimize the number of dependencies in your agent. This reduces the number of breaking changes when updating your dependencies and agent.

If the agent doesn't have any dependencies, you can set requirements to None:



requirements = None
If the agent uses a framework-specific template, you should specify the SDK version that is imported (such as 1.77.0) when developing the agent.

ADK
LangChain
LangGraph
AG2
LlamaIndex

Preview

This feature is subject to the "Pre-GA Offerings Terms" in the General Service Terms section of the Service Specific Terms. Pre-GA features are available "as is" and might have limited support. For more information, see the launch stage descriptions.



requirements = [
    "google-cloud-aiplatform[agent_engines,adk]",
    # any other dependencies
]
You can also do the following with package requirements:

Upper-bound or pin the version of a given package (such as google-cloud-aiplatform):



requirements = [
    # See https://pypi.org/project/google-cloud-aiplatform for the latest version.
    "google-cloud-aiplatform[agent_engines,adk]==1.88.0",
]
Add additional packages and constraints:



requirements = [
    "google-cloud-aiplatform[agent_engines,adk]==1.88.0",
    "cloudpickle==3.0", # new
]
Point to the version of a package on a GitHub branch or pull request:



requirements = [
    "google-cloud-aiplatform[agent_engines,adk] @ git+https://github.com/googleapis/python-aiplatform.git@BRANCH_NAME", # new
    "cloudpickle==3.0",
]
Maintain the list of requirements in a file (such as path/to/requirements.txt):



requirements = "path/to/requirements.txt"
where path/to/requirements.txt is a text file that follows the Requirements File Format. For example:



google-cloud-aiplatform[agent_engines,adk]
cloudpickle==3.0
Define additional packages
You can include local files or directories that contain local required Python source files. Compared to package requirements, this lets you use private utilities you have developed that aren't otherwise available on PyPI or GitHub.

If the agent does not require any extra packages, you can set extra_packages to None:



extra_packages = None
You can also do the following with extra_packages:

Include a single file (such as agents/agent.py):



extra_packages = ["agents/agent.py"]
Include the set of files in an entire directory (for example, agents/):



extra_packages = ["agents"] # directory that includes agents/agent.py
Specify Python wheel binaries (for example, path/to/python_package.whl):



requirements = [
    "google-cloud-aiplatform[agent_engines,adk]",
    "cloudpickle==3.0",
    "python_package.whl",  # install from the whl file that was uploaded
]
extra_packages = ["path/to/python_package.whl"]  # bundle the whl file for uploading
Define environment variables
If there are environment variables that your agent depends on, you can specify them in the env_vars= argument. If the agent does not depend on any environment variables, you can set it to None:



env_vars = None
Warning: You shouldn't set the following environment variables: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_QUOTA_PROJECT, GOOGLE_CLOUD_LOCATION, PORT, K_SERVICE, K_REVISION, K_CONFIGURATION, and GOOGLE_APPLICATION_CREDENTIALS. Also, you should avoid the prefix GOOGLE_CLOUD_AGENT_ENGINE to avoid naming conflicts with Vertex AI Agent Engine environment variables.
To specify the environment variables, there are a few different options available:

Dictionary
List


env_vars = {
  "VARIABLE_1": "VALUE_1",
  "VARIABLE_2": "VALUE_2",
}
# These environment variables will become available in Vertex AI Agent Engine
# through `os.environ`, e.g.
#
#   import os
#   os.environ["VARIABLE_1"] # will have the value "VALUE_1"
#
# and
#
#   os.environ["VARIABLE_2"] # will have the value "VALUE_2"
#
To reference a secret in Secret Manager and have it be available as an environment variable (for example, CLOUD_SQL_CREDENTIALS_SECRET), first follow the instructions to Create a secret for CLOUD_SQL_CREDENTIALS_SECRET in your project, before specifying the environment variables as:



env_vars = {
  # ... (other environment variables and their values)
  "CLOUD_SQL_CREDENTIALS_SECRET": {"secret": "SECRET_ID", "version": "SECRET_VERSION_ID"},
}
where

SECRET_VERSION_ID is the ID of the secret version.
SECRET_ID is the ID of the secret.
Note: You can only reference secrets (and their versions) that are managed in the same project as the deployed agent.
In your agent code, you can then reference the secret like so:



secret = os.environ.get("CLOUD_SQL_CREDENTIALS_SECRET")
if secret:
  # Secrets are stored as strings, so use json.loads to parse JSON payloads.
  return json.loads(secret)
Define build options
You can specify build options for the agent, such as installation scripts to run when building the agent's container image. This is useful for installing system dependencies (for example, gcloud cli, npx) or other custom setups.

To use installation scripts, create a directory named installation_scripts and place your shell scripts inside the directory:



.
├── ...
└── installation_scripts/
    └── install.sh
Next, specify the installation_scripts directory in extra_packages and the script paths in build_options:



extra_packages = [..., "installation_scripts/install.sh"]
build_options = {"installation_scripts": ["installation_scripts/install.sh"]}
Define a Cloud Storage folder
Staging artifacts are overwritten if they correspond to an existing folder in a Cloud Storage bucket. If necessary, you can specify the Cloud Storage folder for the staging artifacts. You can set gcs_dir_name to None if you don't mind potentially overwriting the files in the default folder:



gcs_dir_name = None
To avoid overwriting the files (such as for different environments such as development, staging, and production), you can set up corresponding folder, and specify the folder to stage the artifact under:



gcs_dir_name = "dev" # or "staging" or "prod"
If you want or need to avoid collisions, you can generate a random uuid:



import uuid
gcs_dir_name = str(uuid.uuid4())
Configure resource metadata
You can set metadata on the ReasoningEngine resource:



display_name = "Currency Exchange Rate Agent (Staging)"

description = """
An agent that has access to tools for looking up the exchange rate.

If you run into any issues, please contact the dev team.
"""
For a full set of the parameters, see the API reference.

Create an AgentEngine instance
To deploy the agent on Vertex AI, use agent_engines.create to pass in the local_agent object along with any optional configurations:



remote_agent = agent_engines.create(
    local_agent,                    # Optional.
    requirements=requirements,      # Optional.
    extra_packages=extra_packages,  # Optional.
    gcs_dir_name=gcs_dir_name,      # Optional.
    display_name=display_name,      # Optional.
    description=description,        # Optional.
    env_vars=env_vars,              # Optional.
    build_options=build_options,    # Optional.
)
Deployment takes a few minutes, during which the following steps happen in the background:

A bundle of the following artifacts are generated locally:

*.pkl a pickle file corresponding to local_agent.
requirements.txt a text file containing the package requirements.
dependencies.tar.gz a tar file containing any extra packages.
The bundle is uploaded to Cloud Storage (under the corresponding folder) for staging the artifacts.

The Cloud Storage URIs for the respective artifacts are specified in the PackageSpec.

The Vertex AI Agent Engine service receives the request and builds containers and starts HTTP servers on the backend.

Deployment latency depends on the total time it takes to install required packages. Once deployed, remote_agent corresponds to an instance of local_agent that is running on Vertex AI and can be queried or deleted. It is separate from local instances of the agent.

Grant the deployed agent permissions
If the deployed agent needs to be granted any additional permissions, follow the instructions in Set up your service agent permissions.

If you defined secrets as environment variables, you need to grant the following permission:

Secret Manager Secret Accessor (roles/secretmanager.secretAccessor)
Get the agent resource ID
Each deployed agent has a unique identifier. You can run the following command to get the resource_name identifier for your deployed agent:



remote_agent.resource_name
The response should look like the following string:



"projects/PROJECT_NUMBER/locations/LOCATION/reasoningEngines/RESOURCE_ID"
where

PROJECT_ID is the Google Cloud project ID where the deployed agent runs.

LOCATION is the region where the deployed agent runs.

RESOURCE_ID is the ID of the deployed agent as a reasoningEngine resource.

## google adk callback documentation
allbacks: Observe, Customize, and Control Agent Behavior¶
Introduction: What are Callbacks and Why Use Them?¶
Callbacks are a cornerstone feature of ADK, providing a powerful mechanism to hook into an agent's execution process. They allow you to observe, customize, and even control the agent's behavior at specific, predefined points without modifying the core ADK framework code.

What are they? In essence, callbacks are standard functions that you define. You then associate these functions with an agent when you create it. The ADK framework automatically calls your functions at key stages, letting you observe or intervene. Think of it like checkpoints during the agent's process:

Before the agent starts its main work on a request, and after it finishes: When you ask an agent to do something (e.g., answer a question), it runs its internal logic to figure out the response.
The Before Agent callback executes right before this main work begins for that specific request.
The After Agent callback executes right after the agent has finished all its steps for that request and has prepared the final result, but just before the result is returned.
This "main work" encompasses the agent's entire process for handling that single request. This might involve deciding to call an LLM, actually calling the LLM, deciding to use a tool, using the tool, processing the results, and finally putting together the answer. These callbacks essentially wrap the whole sequence from receiving the input to producing the final output for that one interaction.
Before sending a request to, or after receiving a response from, the Large Language Model (LLM): These callbacks (Before Model, After Model) allow you to inspect or modify the data going to and coming from the LLM specifically.
Before executing a tool (like a Python function or another agent) or after it finishes: Similarly, Before Tool and After Tool callbacks give you control points specifically around the execution of tools invoked by the agent.
intro_components.png

Why use them? Callbacks unlock significant flexibility and enable advanced agent capabilities:

Observe & Debug: Log detailed information at critical steps for monitoring and troubleshooting.
Customize & Control: Modify data flowing through the agent (like LLM requests or tool results) or even bypass certain steps entirely based on your logic.
Implement Guardrails: Enforce safety rules, validate inputs/outputs, or prevent disallowed operations.
Manage State: Read or dynamically update the agent's session state during execution.
Integrate & Enhance: Trigger external actions (API calls, notifications) or add features like caching.
How are they added:

Code
The Callback Mechanism: Interception and Control¶
When the ADK framework encounters a point where a callback can run (e.g., just before calling the LLM), it checks if you provided a corresponding callback function for that agent. If you did, the framework executes your function.

Context is Key: Your callback function isn't called in isolation. The framework provides special context objects (CallbackContext or ToolContext) as arguments. These objects contain vital information about the current state of the agent's execution, including the invocation details, session state, and potentially references to services like artifacts or memory. You use these context objects to understand the situation and interact with the framework. (See the dedicated "Context Objects" section for full details).

Controlling the Flow (The Core Mechanism): The most powerful aspect of callbacks lies in how their return value influences the agent's subsequent actions. This is how you intercept and control the execution flow:

return None (Allow Default Behavior):

The specific return type can vary depending on the language. In Java, the equivalent return type is Optional.empty(). Refer to the API documentation for language specific guidance.
This is the standard way to signal that your callback has finished its work (e.g., logging, inspection, minor modifications to mutable input arguments like llm_request) and that the ADK agent should proceed with its normal operation.
For before_* callbacks (before_agent, before_model, before_tool), returning None means the next step in the sequence (running the agent logic, calling the LLM, executing the tool) will occur.
For after_* callbacks (after_agent, after_model, after_tool), returning None means the result just produced by the preceding step (the agent's output, the LLM's response, the tool's result) will be used as is.
return <Specific Object> (Override Default Behavior):

Returning a specific type of object (instead of None) is how you override the ADK agent's default behavior. The framework will use the object you return and skip the step that would normally follow or replace the result that was just generated.
before_agent_callback → types.Content: Skips the agent's main execution logic (_run_async_impl / _run_live_impl). The returned Content object is immediately treated as the agent's final output for this turn. Useful for handling simple requests directly or enforcing access control.
before_model_callback → LlmResponse: Skips the call to the external Large Language Model. The returned LlmResponse object is processed as if it were the actual response from the LLM. Ideal for implementing input guardrails, prompt validation, or serving cached responses.
before_tool_callback → dict or Map: Skips the execution of the actual tool function (or sub-agent). The returned dict is used as the result of the tool call, which is then typically passed back to the LLM. Perfect for validating tool arguments, applying policy restrictions, or returning mocked/cached tool results.
after_agent_callback → types.Content: Replaces the Content that the agent's run logic just produced.
after_model_callback → LlmResponse: Replaces the LlmResponse received from the LLM. Useful for sanitizing outputs, adding standard disclaimers, or modifying the LLM's response structure.
after_tool_callback → dict or Map: Replaces the dict result returned by the tool. Allows for post-processing or standardization of tool outputs before they are sent back to the LLM.
Conceptual Code Example (Guardrail):

This example demonstrates the common pattern for a guardrail using before_model_callback.

Code
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.adk.runners import Runner
from typing import Optional
from google.genai import types 
from google.adk.sessions import InMemorySessionService

GEMINI_2_FLASH="gemini-2.0-flash"

# --- Define the Callback Function ---
def simple_before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}")

    # Inspect the last user message in the request contents
    last_user_message = ""
    if llm_request.contents and llm_request.contents[-1].role == 'user':
         if llm_request.contents[-1].parts:
            last_user_message = llm_request.contents[-1].parts[0].text
    print(f"[Callback] Inspecting last user message: '{last_user_message}'")

    # --- Modification Example ---
    # Add a prefix to the system instruction
    original_instruction = llm_request.config.system_instruction or types.Content(role="system", parts=[])
    prefix = "[Modified by Callback] "
    # Ensure system_instruction is Content and parts list exists
    if not isinstance(original_instruction, types.Content):
         # Handle case where it might be a string (though config expects Content)
         original_instruction = types.Content(role="system", parts=[types.Part(text=str(original_instruction))])
    if not original_instruction.parts:
        original_instruction.parts.append(types.Part(text="")) # Add an empty part if none exist

    # Modify the text of the first part
    modified_text = prefix + (original_instruction.parts[0].text or "")
    original_instruction.parts[0].text = modified_text
    llm_request.config.system_instruction = original_instruction
    print(f"[Callback] Modified system instruction to: '{modified_text}'")

    # --- Skip Example ---
    # Check if the last user message contains "BLOCK"
    if "BLOCK" in last_user_message.upper():
        print("[Callback] 'BLOCK' keyword found. Skipping LLM call.")
        # Return an LlmResponse to skip the actual LLM call
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="LLM call was blocked by before_model_callback.")],
            )
        )
    else:
        print("[Callback] Proceeding with LLM call.")
        # Return None to allow the (modified) request to go to the LLM
        return None


# Create LlmAgent and Assign Callback
my_llm_agent = LlmAgent(
        name="ModelCallbackAgent",
        model=GEMINI_2_FLASH,
        instruction="You are a helpful assistant.", # Base instruction
        description="An LLM agent demonstrating before_model_callback",
        before_model_callback=simple_before_model_modifier # Assign the function here
)

APP_NAME = "guardrail_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=my_llm_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("write a joke on BLOCK")

By understanding this mechanism of returning None versus returning specific objects, you can precisely control the agent's execution path, making callbacks an essential tool for building sophisticated and reliable agents with ADK.

Types of Callbacks¶
The framework provides different types of callbacks that trigger at various stages of an agent's execution. Understanding when each callback fires and what context it receives is key to using them effectively.

Agent Lifecycle Callbacks¶
These callbacks are available on any agent that inherits from BaseAgent (including LlmAgent, SequentialAgent, ParallelAgent, LoopAgent, etc).

Note

The specific method names or return types may vary slightly by SDK language (e.g., return None in Python, return Optional.empty() or Maybe.empty() in Java). Refer to the language-specific API documentation for details.

Before Agent Callback¶
When: Called immediately before the agent's _run_async_impl (or _run_live_impl) method is executed. It runs after the agent's InvocationContext is created but before its core logic begins.

Purpose: Ideal for setting up resources or state needed only for this specific agent's run, performing validation checks on the session state (callback_context.state) before execution starts, logging the entry point of the agent's activity, or potentially modifying the invocation context before the core logic uses it.

Code
Note on the before_agent_callback Example:

What it Shows: This example demonstrates the before_agent_callback. This callback runs right before the agent's main processing logic starts for a given request.
How it Works: The callback function (check_if_agent_should_run) looks at a flag (skip_llm_agent) in the session's state.
If the flag is True, the callback returns a types.Content object. This tells the ADK framework to skip the agent's main execution entirely and use the callback's returned content as the final response.
If the flag is False (or not set), the callback returns None or an empty object. This tells the ADK framework to proceed with the agent's normal execution (calling the LLM in this case).
Expected Outcome: You'll see two scenarios:
In the session with the skip_llm_agent: True state, the agent's LLM call is bypassed, and the output comes directly from the callback ("Agent... skipped...").
In the session without that state flag, the callback allows the agent to run, and you see the actual response from the LLM (e.g., "Hello!").
Understanding Callbacks: This highlights how before_ callbacks act as gatekeepers, allowing you to intercept execution before a major step and potentially prevent it based on checks (like state, input validation, permissions).
After Agent Callback¶
When: Called immediately after the agent's _run_async_impl (or _run_live_impl) method successfully completes. It does not run if the agent was skipped due to before_agent_callback returning content or if end_invocation was set during the agent's run.

Purpose: Useful for cleanup tasks, post-execution validation, logging the completion of an agent's activity, modifying final state, or augmenting/replacing the agent's final output.

Code
Note on the after_agent_callback Example:

What it Shows: This example demonstrates the after_agent_callback. This callback runs right after the agent's main processing logic has finished and produced its result, but before that result is finalized and returned.
How it Works: The callback function (modify_output_after_agent) checks a flag (add_concluding_note) in the session's state.
If the flag is True, the callback returns a new types.Content object. This tells the ADK framework to replace the agent's original output with the content returned by the callback.
If the flag is False (or not set), the callback returns None or an empty object. This tells the ADK framework to use the original output generated by the agent.
Expected Outcome: You'll see two scenarios:
In the session without the add_concluding_note: True state, the callback allows the agent's original output ("Processing complete!") to be used.
In the session with that state flag, the callback intercepts the agent's original output and replaces it with its own message ("Concluding note added...").
Understanding Callbacks: This highlights how after_ callbacks allow post-processing or modification. You can inspect the result of a step (the agent's run) and decide whether to let it pass through, change it, or completely replace it based on your logic.
LLM Interaction Callbacks¶
These callbacks are specific to LlmAgent and provide hooks around the interaction with the Large Language Model.

Before Model Callback¶
When: Called just before the generate_content_async (or equivalent) request is sent to the LLM within an LlmAgent's flow.

Purpose: Allows inspection and modification of the request going to the LLM. Use cases include adding dynamic instructions, injecting few-shot examples based on state, modifying model config, implementing guardrails (like profanity filters), or implementing request-level caching.

Return Value Effect:
If the callback returns None (or a Maybe.empty() object in Java), the LLM continues its normal workflow. If the callback returns an LlmResponse object, then the call to the LLM is skipped. The returned LlmResponse is used directly as if it came from the model. This is powerful for implementing guardrails or caching.

Code
After Model Callback¶
When: Called just after a response (LlmResponse) is received from the LLM, before it's processed further by the invoking agent.

Purpose: Allows inspection or modification of the raw LLM response. Use cases include

logging model outputs,
reformatting responses,
censoring sensitive information generated by the model,
parsing structured data from the LLM response and storing it in callback_context.state
or handling specific error codes.
Code
Tool Execution Callbacks¶
These callbacks are also specific to LlmAgent and trigger around the execution of tools (including FunctionTool, AgentTool, etc.) that the LLM might request.

Before Tool Callback¶
When: Called just before a specific tool's run_async method is invoked, after the LLM has generated a function call for it.

Purpose: Allows inspection and modification of tool arguments, performing authorization checks before execution, logging tool usage attempts, or implementing tool-level caching.

Return Value Effect:

If the callback returns None (or a Maybe.empty() object in Java), the tool's run_async method is executed with the (potentially modified) args.
If a dictionary (or Map in Java) is returned, the tool's run_async method is skipped. The returned dictionary is used directly as the result of the tool call. This is useful for caching or overriding tool behavior.
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from typing import Optional
from google.genai import types 
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from typing import Dict, Any


GEMINI_2_FLASH="gemini-2.0-flash"

def get_capital_city(country: str) -> str:
    """Retrieves the capital city of a given country."""
    print(f"--- Tool 'get_capital_city' executing with country: {country} ---")
    country_capitals = {
        "united states": "Washington, D.C.",
        "canada": "Ottawa",
        "france": "Paris",
        "germany": "Berlin",
    }
    return country_capitals.get(country.lower(), f"Capital not found for {country}")

capital_tool = FunctionTool(func=get_capital_city)

def simple_before_tool_modifier(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """Inspects/modifies tool args or skips the tool call."""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    print(f"[Callback] Before tool call for tool '{tool_name}' in agent '{agent_name}'")
    print(f"[Callback] Original args: {args}")

    if tool_name == 'get_capital_city' and args.get('country', '').lower() == 'canada':
        print("[Callback] Detected 'Canada'. Modifying args to 'France'.")
        args['country'] = 'France'
        print(f"[Callback] Modified args: {args}")
        return None

    # If the tool is 'get_capital_city' and country is 'BLOCK'
    if tool_name == 'get_capital_city' and args.get('country', '').upper() == 'BLOCK':
        print("[Callback] Detected 'BLOCK'. Skipping tool execution.")
        return {"result": "Tool execution was blocked by before_tool_callback."}

    print("[Callback] Proceeding with original or previously modified args.")
    return None

my_llm_agent = LlmAgent(
        name="ToolCallbackAgent",
        model=GEMINI_2_FLASH,
        instruction="You are an agent that can find capital cities. Use the get_capital_city tool.",
        description="An LLM agent demonstrating before_tool_callback",
        tools=[capital_tool],
        before_tool_callback=simple_before_tool_modifier
)

APP_NAME = "guardrail_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=my_llm_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner

# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("Canada")

fter Tool Callback¶
When: Called just after the tool's run_async method completes successfully.

Purpose: Allows inspection and modification of the tool's result before it's sent back to the LLM (potentially after summarization). Useful for logging tool results, post-processing or formatting results, or saving specific parts of the result to the session state.

Return Value Effect:

If the callback returns None (or a Maybe.empty() object in Java), the original tool_response is used.
If a new dictionary is returned, it replaces the original tool_response. This allows modifying or filtering the result seen by the LLM.
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from typing import Optional
from google.genai import types 
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.base_tool import BaseTool
from typing import Dict, Any
from copy import deepcopy

GEMINI_2_FLASH="gemini-2.0-flash"

# --- Define a Simple Tool Function (Same as before) ---
def get_capital_city(country: str) -> str:
    """Retrieves the capital city of a given country."""
    print(f"--- Tool 'get_capital_city' executing with country: {country} ---")
    country_capitals = {
        "united states": "Washington, D.C.",
        "canada": "Ottawa",
        "france": "Paris",
        "germany": "Berlin",
    }
    return {"result": country_capitals.get(country.lower(), f"Capital not found for {country}")}

# --- Wrap the function into a Tool ---
capital_tool = FunctionTool(func=get_capital_city)

# --- Define the Callback Function ---
def simple_after_tool_modifier(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """Inspects/modifies the tool result after execution."""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    print(f"[Callback] After tool call for tool '{tool_name}' in agent '{agent_name}'")
    print(f"[Callback] Args used: {args}")
    print(f"[Callback] Original tool_response: {tool_response}")

    # Default structure for function tool results is {"result": <return_value>}
    original_result_value = tool_response.get("result", "")
    # original_result_value = tool_response

    # --- Modification Example ---
    # If the tool was 'get_capital_city' and result is 'Washington, D.C.'
    if tool_name == 'get_capital_city' and original_result_value == "Washington, D.C.":
        print("[Callback] Detected 'Washington, D.C.'. Modifying tool response.")

        # IMPORTANT: Create a new dictionary or modify a copy
        modified_response = deepcopy(tool_response)
        modified_response["result"] = f"{original_result_value} (Note: This is the capital of the USA)."
        modified_response["note_added_by_callback"] = True # Add extra info if needed

        print(f"[Callback] Modified tool_response: {modified_response}")
        return modified_response # Return the modified dictionary

    print("[Callback] Passing original tool response through.")
    # Return None to use the original tool_response
    return None


# Create LlmAgent and Assign Callback
my_llm_agent = LlmAgent(
        name="AfterToolCallbackAgent",
        model=GEMINI_2_FLASH,
        instruction="You are an agent that finds capital cities using the get_capital_city tool. Report the result clearly.",
        description="An LLM agent demonstrating after_tool_callback",
        tools=[capital_tool], # Add the tool
        after_tool_callback=simple_after_tool_modifier # Assign the callback
    )

APP_NAME = "guardrail_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# Session and Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)
    runner = Runner(agent=my_llm_agent, app_name=APP_NAME, session_service=session_service)
    return session, runner


# Agent Interaction
async def call_agent_async(query):
    content = types.Content(role='user', parts=[types.Part(text=query)])
    session, runner = await setup_session_and_runner()
    events = runner.run_async(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)

# Note: In Colab, you can directly use 'await' at the top level.
# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
await call_agent_async("united states")

Design Patterns and Best Practices for Callbacks¶
Callbacks offer powerful hooks into the agent lifecycle. Here are common design patterns illustrating how to leverage them effectively in ADK, followed by best practices for implementation.

Design Patterns¶
These patterns demonstrate typical ways to enhance or control agent behavior using callbacks:

1. Guardrails & Policy Enforcement¶
Pattern: Intercept requests before they reach the LLM or tools to enforce rules.
How: Use before_model_callback to inspect the LlmRequest prompt or before_tool_callback to inspect tool arguments. If a policy violation is detected (e.g., forbidden topics, profanity), return a predefined response (LlmResponse or dict/ Map) to block the operation and optionally update context.state to log the violation.
Example: A before_model_callback checks llm_request.contents for sensitive keywords and returns a standard "Cannot process this request" LlmResponse if found, preventing the LLM call.
2. Dynamic State Management¶
Pattern: Read from and write to session state within callbacks to make agent behavior context-aware and pass data between steps.
How: Access callback_context.state or tool_context.state. Modifications (state['key'] = value) are automatically tracked in the subsequent Event.actions.state_delta for persistence by the SessionService.
Example: An after_tool_callback saves a transaction_id from the tool's result to tool_context.state['last_transaction_id']. A later before_agent_callback might read state['user_tier'] to customize the agent's greeting.
3. Logging and Monitoring¶
Pattern: Add detailed logging at specific lifecycle points for observability and debugging.
How: Implement callbacks (e.g., before_agent_callback, after_tool_callback, after_model_callback) to print or send structured logs containing information like agent name, tool name, invocation ID, and relevant data from the context or arguments.
Example: Log messages like INFO: [Invocation: e-123] Before Tool: search_api - Args: {'query': 'ADK'}.
4. Caching¶
Pattern: Avoid redundant LLM calls or tool executions by caching results.
How: In before_model_callback or before_tool_callback, generate a cache key based on the request/arguments. Check context.state (or an external cache) for this key. If found, return the cached LlmResponse or result directly, skipping the actual operation. If not found, allow the operation to proceed and use the corresponding after_ callback (after_model_callback, after_tool_callback) to store the new result in the cache using the key.
Example: before_tool_callback for get_stock_price(symbol) checks state[f"cache:stock:{symbol}"]. If present, returns the cached price; otherwise, allows the API call and after_tool_callback saves the result to the state key.
5. Request/Response Modification¶
Pattern: Alter data just before it's sent to the LLM/tool or just after it's received.
How:
before_model_callback: Modify llm_request (e.g., add system instructions based on state).
after_model_callback: Modify the returned LlmResponse (e.g., format text, filter content).
before_tool_callback: Modify the tool args dictionary (or Map in Java).
after_tool_callback: Modify the tool_response dictionary (or Map in Java).
Example: before_model_callback appends "User language preference: Spanish" to llm_request.config.system_instruction if context.state['lang'] == 'es'.
6. Conditional Skipping of Steps¶
Pattern: Prevent standard operations (agent run, LLM call, tool execution) based on certain conditions.
How: Return a value from a before_ callback (Content from before_agent_callback, LlmResponse from before_model_callback, dict from before_tool_callback). The framework interprets this returned value as the result for that step, skipping the normal execution.
Example: before_tool_callback checks tool_context.state['api_quota_exceeded']. If True, it returns {'error': 'API quota exceeded'}, preventing the actual tool function from running.
7. Tool-Specific Actions (Authentication & Summarization Control)¶
Pattern: Handle actions specific to the tool lifecycle, primarily authentication and controlling LLM summarization of tool results.
How: Use ToolContext within tool callbacks (before_tool_callback, after_tool_callback).
Authentication: Call tool_context.request_credential(auth_config) in before_tool_callback if credentials are required but not found (e.g., via tool_context.get_auth_response or state check). This initiates the auth flow.
Summarization: Set tool_context.actions.skip_summarization = True if the raw dictionary output of the tool should be passed back to the LLM or potentially displayed directly, bypassing the default LLM summarization step.
Example: A before_tool_callback for a secure API checks for an auth token in state; if missing, it calls request_credential. An after_tool_callback for a tool returning structured JSON might set skip_summarization = True.
8. Artifact Handling¶
Pattern: Save or load session-related files or large data blobs during the agent lifecycle.
How: Use callback_context.save_artifact / await tool_context.save_artifact to store data (e.g., generated reports, logs, intermediate data). Use load_artifact to retrieve previously stored artifacts. Changes are tracked via Event.actions.artifact_delta.
Example: An after_tool_callback for a "generate_report" tool saves the output file using await tool_context.save_artifact("report.pdf", report_part). A before_agent_callback might load a configuration artifact using callback_context.load_artifact("agent_config.json").
Best Practices for Callbacks¶
Keep Focused: Design each callback for a single, well-defined purpose (e.g., just logging, just validation). Avoid monolithic callbacks.
Mind Performance: Callbacks execute synchronously within the agent's processing loop. Avoid long-running or blocking operations (network calls, heavy computation). Offload if necessary, but be aware this adds complexity.
Handle Errors Gracefully: Use try...except/ catch blocks within your callback functions. Log errors appropriately and decide if the agent invocation should halt or attempt recovery. Don't let callback errors crash the entire process.
Manage State Carefully:
Be deliberate about reading from and writing to context.state. Changes are immediately visible within the current invocation and persisted at the end of the event processing.
Use specific state keys rather than modifying broad structures to avoid unintended side effects.
Consider using state prefixes (State.APP_PREFIX, State.USER_PREFIX, State.TEMP_PREFIX) for clarity, especially with persistent SessionService implementations.
Consider Idempotency: If a callback performs actions with external side effects (e.g., incrementing an external counter), design it to be idempotent (safe to run multiple times with the same input) if possible, to handle potential retries in the framework or your application.
Test Thoroughly: Unit test your callback functions using mock context objects. Perform integration tests to ensure callbacks function correctly within the full agent flow.
Ensure Clarity: Use descriptive names for your callback functions. Add clear docstrings explaining their purpose, when they run, and any side effects (especially state modifications).
Use Correct Context Type: Always use the specific context type provided (CallbackContext for agent/model, ToolContext for tools) to ensure access to the appropriate methods and properties.
By applying these patterns and best practices, you can effectively use callbacks to create more robust, observable, and customized agent behaviors in ADK.

