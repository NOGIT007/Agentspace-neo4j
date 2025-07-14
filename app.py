import os
import json
import asyncio
import subprocess
import requests
import importlib
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from vertexai.preview.reasoning_engines import ReasoningEngine, AdkApp
import vertexai
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Agent configurations - Add new agents here
AGENT_CONFIGS = {
    "neo4j": {
        "module": "agents.agent",
        "attribute": "root_agent",
        "display_name": "Neo4j Query Agent",
        "description": "Query Neo4j databases using natural language",
        "requirements": ["neo4j>=5.0.0"],
        "env_vars": {
            "NEO4J_URI": {"required": True, "description": "Neo4j database URI"},
            "NEO4J_USERNAME": {"required": True, "description": "Neo4j username"},
            "NEO4J_PASSWORD": {"required": True, "description": "Neo4j password"},
            "NEO4J_DATABASE": {"required": False, "default": "neo4j", "description": "Neo4j database name"}
        },
        "extra_packages": ["agents/agent.py"],
        "test_message": "Test connection to database",
        "tool_description": "Query Neo4j database using natural language. This tool can retrieve nodes, relationships, and execute complex graph queries."
    }
    # Add more agent configurations here as needed
}

# Global variables
deployed_agent_resource_name = None
selected_agent_type = "neo4j"  # Default agent type
deployment_progress = {
    'status': 'idle',
    'step': 0,
    'message': '',
    'total_steps': 4
}

# Helper functions for Agentspace operations
def get_access_token():
    """Get Google Cloud access token using gcloud."""
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'print-access-token'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get access token: {e}")
        raise Exception("Failed to authenticate with Google Cloud. Please run 'gcloud auth login'")

def make_agentspace_request(method, url, headers=None, json_data=None, timeout=30):
    """Make HTTP request to Agentspace API with proper error handling."""
    if headers is None:
        headers = {}
    
    # Add authorization header
    try:
        access_token = get_access_token()
        headers['Authorization'] = f'Bearer {access_token}'
    except Exception as e:
        return None, str(e)
    
    # Add default headers
    headers['Content-Type'] = 'application/json'
    if 'X-Goog-User-Project' not in headers:
        headers['X-Goog-User-Project'] = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            timeout=timeout
        )
        
        # Log the response for debugging
        logging.info(f"{method} {url} - Status: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = response.text
        
        if response.status_code in [200, 201]:
            return response_data, None
        else:
            error_msg = response_data if isinstance(response_data, str) else response_data.get('error', {}).get('message', 'Unknown error')
            return None, f"API Error ({response.status_code}): {error_msg}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out"
    except requests.exceptions.ConnectionError:
        return None, "Failed to connect to Agentspace API"
    except Exception as e:
        return None, f"Request failed: {str(e)}"

def get_current_agent_config():
    """Get the configuration for the currently selected agent."""
    return AGENT_CONFIGS.get(selected_agent_type, AGENT_CONFIGS["neo4j"])

def load_agent_dynamically(agent_config):
    """Dynamically load an agent based on configuration."""
    try:
        module = importlib.import_module(agent_config["module"])
        agent = getattr(module, agent_config["attribute"])
        return agent
    except Exception as e:
        logging.error(f"Failed to load agent: {e}")
        raise Exception(f"Failed to load agent from {agent_config['module']}.{agent_config['attribute']}: {str(e)}")

@app.route('/')
def index():
    """Render the main UI."""
    return render_template('index.html')

@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration from environment variables."""
    try:
        config = {
            'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
            'location': os.getenv('GOOGLE_CLOUD_LOCATION', 'europe-west1'),
            'model': os.getenv('MODEL_NAME', 'gemini-2.5-flash'),
            'agentspace_id': os.getenv('APP_ID'),
            'project_number': os.getenv('GOOGLE_CLOUD_PROJECT_NUMBER', '881765721010'),
            'storage_bucket': os.getenv('GOOGLE_CLOUD_STORAGE'),
            'selected_agent': selected_agent_type,
            'agent_config': get_current_agent_config()
        }
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/agent_types', methods=['GET'])
def get_agent_types():
    """Get available agent types and their configurations."""
    try:
        agent_list = []
        for agent_type, config in AGENT_CONFIGS.items():
            agent_info = {
                'type': agent_type,
                'display_name': config['display_name'],
                'description': config['description'],
                'selected': agent_type == selected_agent_type
            }
            agent_list.append(agent_info)
        
        return jsonify({
            'success': True,
            'agents': agent_list,
            'selected': selected_agent_type
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/select_agent', methods=['POST'])
def select_agent():
    """Select an agent type for deployment."""
    global selected_agent_type
    
    try:
        data = request.json
        agent_type = data.get('agent_type')
        
        if agent_type not in AGENT_CONFIGS:
            return jsonify({
                'success': False,
                'error': f'Unknown agent type: {agent_type}'
            }), 400
        
        selected_agent_type = agent_type
        agent_config = get_current_agent_config()
        
        # Check if required environment variables are set
        missing_vars = []
        for var_name, var_config in agent_config.get('env_vars', {}).items():
            if var_config.get('required', False) and not os.getenv(var_name):
                missing_vars.append(var_name)
        
        return jsonify({
            'success': True,
            'message': f'Selected agent: {agent_config["display_name"]}',
            'agent_type': agent_type,
            'agent_config': agent_config,
            'missing_env_vars': missing_vars
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/deploy/progress', methods=['GET'])
def get_deployment_progress():
    """Get current deployment progress."""
    global deployment_progress
    
    # If status is idle and someone is polling, reset it properly
    if deployment_progress.get('status') == 'idle':
        deployment_progress = {
            'status': 'idle',
            'step': 0,
            'message': '',
            'total_steps': 4
        }
    
    return jsonify(deployment_progress)

@app.route('/deploy/reset', methods=['POST'])
def reset_deployment_progress():
    """Reset deployment progress to idle state."""
    global deployment_progress
    deployment_progress = {
        'status': 'idle',
        'step': 0,
        'message': '',
        'total_steps': 4
    }
    return jsonify({'success': True, 'message': 'Deployment progress reset'})

@app.route('/test_connection', methods=['POST'])
def test_connection():
    """Test basic connection and configuration."""
    try:
        data = request.json or {}
        
        # Test basic configuration
        project_id = data.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
        location = data.get('location') or os.getenv('GOOGLE_CLOUD_LOCATION', 'europe-west1')
        storage_bucket = data.get('storage_bucket') or os.getenv('GOOGLE_CLOUD_STORAGE')
        
        if not project_id:
            return jsonify({'success': False, 'error': 'No project ID configured'}), 400
        
        if not storage_bucket:
            return jsonify({'success': False, 'error': 'No storage bucket configured'}), 400
        
        # Test Vertex AI initialization
        vertexai.init(project=project_id, location=location, staging_bucket=storage_bucket)
        
        # Test agent import
        from agents.agent import root_agent
        
        return jsonify({
            'success': True,
            'message': 'Configuration test passed',
            'config': {
                'project_id': project_id,
                'location': location,
                'storage_bucket': storage_bucket,
                'agent_loaded': True
            }
        })
        
    except Exception as e:
        logging.error(f"Configuration test failed: {e}")
        return jsonify({
            'success': False,
            'error': f'Configuration test failed: {str(e)}'
        }), 500

@app.route('/deploy', methods=['POST'])
def deploy_agent():
    """Deploy the agent to Vertex AI Agent Engine."""
    global deployment_progress, deployed_agent_resource_name
    
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        agent_name = data.get('agent_name', os.getenv('AGENT_NAME', 'agent'))
        logging.info(f"Starting deployment for agent: {agent_name}")
        
        # Reset progress
        deployment_progress = {
            'status': 'running',
            'step': 1,
            'message': '🔧 Step 1: Initializing deployment configuration...',
            'total_steps': 5
        }
        
        # Get environment variables with overrides from request
        project_id = data.get('project_id') or os.getenv('GOOGLE_CLOUD_PROJECT')
        location = data.get('location') or os.getenv('GOOGLE_CLOUD_LOCATION', 'europe-west1')
        model_name = data.get('model_name') or os.getenv('MODEL_NAME', 'gemini-2.5-flash')
        storage_bucket = data.get('storage_bucket') or os.getenv('GOOGLE_CLOUD_STORAGE')
        
        # Initialize Vertex AI with staging bucket
        vertexai.init(project=project_id, location=location, staging_bucket=storage_bucket)
        
        # Get current agent configuration
        agent_config = get_current_agent_config()
        
        # Define requirements according to Agent Engine documentation
        deployment_requirements = [
            "google-cloud-aiplatform[agent_engines,adk]",  # Don't pin to avoid version conflicts
            "google-adk>=0.1.0",  # Ensure ADK is available
            "python-dotenv>=0.19.0",
            "google-genai>=0.8.0"  # Add explicit genai dependency
        ]
        
        # Add agent-specific requirements
        deployment_requirements.extend(agent_config.get('requirements', []))
        
        # Load the agent dynamically
        try:
            selected_agent = load_agent_dynamically(agent_config)
        except Exception as e:
            deployment_progress.update({
                'status': 'failed',
                'message': f'❌ Failed to load agent: {str(e)}'
            })
            return jsonify({
                'success': False,
                'error': f'Failed to load agent: {str(e)}'
            }), 500
        
        # Prepare environment variables for deployment
        # WARNING: Don't set GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION per documentation
        deployment_env_vars = {
            "MODEL_NAME": model_name,
            "GOOGLE_GENAI_USE_VERTEXAI": "True"
        }
        
        # Add agent-specific environment variables
        for var_name, var_config in agent_config.get('env_vars', {}).items():
            env_value = os.getenv(var_name)
            if env_value:
                deployment_env_vars[var_name] = env_value
            elif var_config.get('default'):
                deployment_env_vars[var_name] = var_config['default']
        
        extra_packages_list = agent_config.get('extra_packages', [])
        
        # Step 1: Wrap agent in deployable ADK App for local testing only
        deployment_progress.update({
            'step': 2,
            'message': '📦 Step 2: Wrapping agent in deployable ADK App for testing...'
        })
        
        # AdkApp is only used for local testing, not for deployment
        deployable_app = AdkApp(
            agent=selected_agent, 
            enable_tracing=True
        )
        
        deployment_progress.update({
            'step': 3,
            'message': '🧪 Step 3: Running final local test...'
        })
        
        # Test the deployable app locally before deployment
        try:
            test_message = agent_config.get('test_message', 'Test agent functionality')
            test_events = list(deployable_app.stream_query(
                user_id="deployment_test_user",
                message=test_message,
            ))
            logging.info(f"✅ Final test completed ({len(test_events)} events).")
            
            # Validate that the test produced some output
            if not test_events:
                raise Exception("Local test produced no events - agent may not be working correctly")
                
        except Exception as test_error:
            logging.error(f"Local test failed: {test_error}")
            deployment_progress.update({
                'status': 'failed',
                'message': f'❌ Local test failed: {str(test_error)}'
            })
            return jsonify({
                'success': False,
                'error': f'Local test failed: {str(test_error)}'
            }), 500
        
        deployment_progress.update({
            'step': 4,
            'message': f'☁️ Step 4: Deploying to Vertex AI Agent Engine...<br>📤 Uploading code and dependencies...<br>🔧 Creating agent service...<br>⚙️ Configuring environment...'
        })
        
        # Deploy to Agent Engine using agent_engines.create for ADK agents
        # This ensures the framework is properly set to "google-adk"
        from vertexai import agent_engines
        import uuid
        unique_gcs_dir = f"agent-{agent_name}-{str(uuid.uuid4())[:8]}"
        
        # According to CLAUDE.md, pass the agent directly with agent_engine parameter
        remote_agent = agent_engines.create(
            agent_engine=selected_agent,  # Use agent_engine parameter name
            display_name=agent_name,
            description=f"{agent_config['display_name']} - deployed via UI",
            requirements=deployment_requirements,
            extra_packages=extra_packages_list,  # Include appropriate agent file
            gcs_dir_name=unique_gcs_dir,  # Use UUID to ensure uniqueness
            env_vars=deployment_env_vars  # Pass env_vars here for agent_engines.create
        )
        
        deployed_agent_resource_name = remote_agent.resource_name
        
        deployment_progress.update({
            'status': 'completed',
            'step': 5,
            'message': '🎉 DEPLOYMENT SUCCESSFUL! 🎉'
        })
        
        return jsonify({
            'success': True,
            'message': f'Agent {agent_name} deployed successfully!',
            'resource_name': deployed_agent_resource_name,
            'region': location,
            'project': project_id,
            'model': model_name
        })
        
    except Exception as e:
        deployment_progress.update({
            'status': 'failed',
            'message': f'❌ Deployment failed: {str(e)}'
        })
        logging.error(f"Deployment failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test', methods=['POST'])
def test_agent():
    """Test the deployed agent using agent_engines."""
    try:
        data = request.json
        query = data.get('query', '')
        resource_name = data.get('resource_name', deployed_agent_resource_name)
        
        if not resource_name:
            return jsonify({
                'success': False,
                'error': 'No agent resource name provided. Deploy an agent first.'
            }), 400
        
        # Initialize Vertex AI
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'europe-west1')
        vertexai.init(project=project_id, location=location)
        
        logging.info(f"Testing agent: {resource_name} with query: {query}")
        
        # Get the deployed agent using agent_engines
        from vertexai import agent_engines
        remote_agent = agent_engines.get(resource_name)
        
        # Test the agent with streaming
        response_parts = []
        logging.info(f"Sending query to deployed agent...")
        
        for event in remote_agent.stream_query(
            user_id="ui_test_user",
            message=query,
        ):
            # Check for text responses
            if ('content' in event and
                'parts' in event['content'] and
                event['content']['parts']):

                for part in event['content']['parts']:
                    if 'text' in part:
                        response_parts.append(part['text'])
                        logging.info(f"Received text response part")
                    elif 'function_call' in part:
                        function_name = part['function_call']['name']
                        logging.info(f"Agent called function: {function_name}")
        
        if response_parts:
            full_response = '\n'.join(response_parts)
            logging.info("Test query successful!")
            return jsonify({
                'success': True,
                'response': full_response
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Agent responded but no text content was found. Check agent logs.'
            })
        
    except Exception as e:
        logging.error(f"Test failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Test failed: {str(e)}"
        }), 500

@app.route('/register', methods=['POST'])
def register_to_agentspace():
    """Register the agent to Agentspace."""
    try:
        data = request.json
        resource_name = data.get('resource_name', deployed_agent_resource_name)
        
        # Get current agent configuration
        agent_config = get_current_agent_config()
        
        # Use agent config defaults if not provided
        agent_display_name = data.get('display_name', agent_config['display_name'])
        agent_description = data.get('description', agent_config['description'])
        icon_uri = data.get('icon_uri', '')  # Optional icon URL
        auth_id = data.get('auth_id', '')  # Optional authentication ID
        
        if not resource_name:
            return jsonify({
                'success': False,
                'error': 'No agent resource name provided. Please deploy an agent first.'
            }), 400
        
        # Get environment variables
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        agentspace_id = data.get('agentspace_id') or os.getenv('APP_ID')
        project_number = os.getenv('GOOGLE_CLOUD_PROJECT_NUMBER', '881765721010')
        
        if not all([project_id, agentspace_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required configuration: GOOGLE_CLOUD_PROJECT or APP_ID'
            }), 400
        
        # Determine location based on configuration
        agentspace_location = 'eu' if 'europe' in os.getenv('GOOGLE_CLOUD_LOCATION', '') else 'global'
        
        logging.info(f"Registering agent to Agentspace: {agentspace_id}")
        logging.info(f"Resource name: {resource_name}")
        
        # Build API URL
        api_url = f"https://{agentspace_location}-discoveryengine.googleapis.com/v1alpha/projects/{project_number}/locations/{agentspace_location}/collections/default_collection/engines/{agentspace_id}/assistants/default_assistant/agents"
        
        # Prepare request payload
        api_data = {
            "displayName": agent_display_name,
            "description": agent_description,
            "adk_agent_definition": {
                "tool_settings": {
                    "tool_description": agent_config.get('tool_description', f"{agent_config['display_name']} tool")
                },
                "provisioned_reasoning_engine": {
                    "reasoning_engine": resource_name
                }
            }
        }
        
        # Add optional fields if provided
        if icon_uri:
            api_data["iconUri"] = icon_uri
        if auth_id:
            api_data["authId"] = auth_id
        
        # Make the API request
        response_data, error = make_agentspace_request(
            method='POST',
            url=api_url,
            json_data=api_data
        )
        
        if error:
            logging.error(f"Registration failed: {error}")
            return jsonify({
                'success': False,
                'error': error
            }), 500
        
        # Extract agent ID from response
        agent_name = response_data.get('name', '')
        agent_id = agent_name.split('/')[-1] if agent_name else None
        
        return jsonify({
            'success': True,
            'message': 'Agent registered to Agentspace successfully!',
            'agent_id': agent_id,
            'agent_name': agent_name,
            'display_name': response_data.get('displayName'),
            'create_time': response_data.get('createTime')
        })
            
    except Exception as e:
        logging.error(f"Registration failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Registration failed: {str(e)}"
        }), 500

@app.route('/delete', methods=['POST'])
def delete_from_agentspace():
    """Delete an agent from Agentspace."""
    try:
        data = request.json
        agent_id = data.get('agent_id')
        
        if not agent_id:
            return jsonify({
                'success': False,
                'error': 'No agent ID provided. Please specify the agent to delete.'
            }), 400
        
        # Get environment variables
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        agentspace_id = data.get('agentspace_id') or os.getenv('APP_ID')
        project_number = os.getenv('GOOGLE_CLOUD_PROJECT_NUMBER', '881765721010')
        
        if not all([project_id, agentspace_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required configuration: GOOGLE_CLOUD_PROJECT or APP_ID'
            }), 400
        
        # Determine location based on configuration
        agentspace_location = 'eu' if 'europe' in os.getenv('GOOGLE_CLOUD_LOCATION', '') else 'global'
        
        logging.info(f"Deleting agent {agent_id} from Agentspace {agentspace_id}")
        
        # Build API URL
        api_url = f"https://{agentspace_location}-discoveryengine.googleapis.com/v1alpha/projects/{project_number}/locations/{agentspace_location}/collections/default_collection/engines/{agentspace_id}/assistants/default_assistant/agents/{agent_id}"
        
        # Make the DELETE request
        response_data, error = make_agentspace_request(
            method='DELETE',
            url=api_url
        )
        
        if error:
            # Check for specific error cases
            if "404" in error:
                return jsonify({
                    'success': False,
                    'error': f"Agent '{agent_id}' not found in Agentspace. It may have already been deleted."
                }), 404
            elif "403" in error:
                return jsonify({
                    'success': False,
                    'error': "Permission denied. Please check your Google Cloud permissions."
                }), 403
            else:
                logging.error(f"Deletion failed: {error}")
                return jsonify({
                    'success': False,
                    'error': error
                }), 500
        
        # Successful deletion (usually returns empty response)
        return jsonify({
            'success': True,
            'message': f'Agent {agent_id} deleted from Agentspace successfully!',
            'agent_id': agent_id
        })
            
    except Exception as e:
        logging.error(f"Deletion failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Deletion failed: {str(e)}"
        }), 500

@app.route('/list_deployed_agents', methods=['GET'])
def list_deployed_agents():
    """List all deployed agents from Vertex AI Agent Engine."""
    try:
        # Get environment variables
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('GOOGLE_CLOUD_LOCATION', 'europe-west1')
        
        if not project_id:
            return jsonify({
                'success': False,
                'error': 'Missing GOOGLE_CLOUD_PROJECT configuration'
            }), 400
        
        logging.info(f"Listing deployed agents from Vertex AI")
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location)
        
        # List all reasoning engines (deployed agents)
        from vertexai import agent_engines
        agents = []
        
        try:
            # Get all reasoning engines
            reasoning_engines = agent_engines.list()
            
            for engine in reasoning_engines:
                agent_info = {
                    'resource_name': engine.resource_name,
                    'display_name': engine.display_name,
                    'description': getattr(engine, 'description', ''),
                    'create_time': str(engine.create_time) if hasattr(engine, 'create_time') else '',
                    'state': getattr(engine, 'state', 'ACTIVE')
                }
                agents.append(agent_info)
                
        except Exception as e:
            logging.warning(f"Could not list reasoning engines: {e}")
        
        return jsonify({
            'success': True,
            'agents': agents,
            'count': len(agents),
            'project': project_id,
            'location': location
        })
        
    except Exception as e:
        logging.error(f"List deployed agents failed: {e}")
        return jsonify({
            'success': False,
            'error': f"Failed to list deployed agents: {str(e)}"
        }), 500

@app.route('/list_agents', methods=['GET'])
def list_agents():
    """List all agents in Agentspace."""
    try:
        # Get environment variables
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        agentspace_id = request.args.get('agentspace_id') or os.getenv('APP_ID')
        project_number = os.getenv('GOOGLE_CLOUD_PROJECT_NUMBER', '881765721010')
        
        if not all([project_id, agentspace_id]):
            return jsonify({
                'success': False,
                'error': 'Missing required configuration: GOOGLE_CLOUD_PROJECT or APP_ID'
            }), 400
        
        # Determine location based on configuration
        agentspace_location = 'eu' if 'europe' in os.getenv('GOOGLE_CLOUD_LOCATION', '') else 'global'
        
        logging.info(f"Listing agents in Agentspace: {agentspace_id}")
        
        # Build API URL
        api_url = f"https://{agentspace_location}-discoveryengine.googleapis.com/v1alpha/projects/{project_number}/locations/{agentspace_location}/collections/default_collection/engines/{agentspace_id}/assistants/default_assistant/agents"
        
        # Make the GET request
        response_data, error = make_agentspace_request(
            method='GET',
            url=api_url
        )
        
        if error:
            # Check for specific error cases
            if "404" in error:
                return jsonify({
                    'success': False,
                    'error': f"Agentspace '{agentspace_id}' not found. Please check your APP_ID configuration."
                }), 404
            elif "403" in error:
                return jsonify({
                    'success': False,
                    'error': "Permission denied. Please check your Google Cloud permissions."
                }), 403
            else:
                logging.error(f"List agents failed: {error}")
                return jsonify({
                    'success': False,
                    'error': error
                }), 500
        
        # Extract agent information
        agents = response_data.get('agents', [])
        agent_list = []
        
        for agent in agents:
            # Extract ADK-specific information
            adk_definition = agent.get('adk_agent_definition', {})
            reasoning_engine = adk_definition.get('provisioned_reasoning_engine', {}).get('reasoning_engine', '')
            
            agent_info = {
                'id': agent.get('name', '').split('/')[-1],
                'displayName': agent.get('displayName', ''),
                'description': agent.get('description', ''),
                'createTime': agent.get('createTime', ''),
                'updateTime': agent.get('updateTime', ''),
                'iconUri': agent.get('iconUri', ''),
                'reasoningEngine': reasoning_engine,
                'toolDescription': adk_definition.get('tool_settings', {}).get('tool_description', '')
            }
            agent_list.append(agent_info)
        
        # Sort by creation time (newest first)
        agent_list.sort(key=lambda x: x.get('createTime', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'agents': agent_list,
            'count': len(agent_list),
            'agentspace_id': agentspace_id
        })
            
    except Exception as e:
        logging.error(f"List agents failed: {e}")
        return jsonify({
            'success': False,
            'error': f"List agents failed: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)