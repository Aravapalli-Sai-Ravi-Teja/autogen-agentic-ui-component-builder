import yaml
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient
import requests
    

class AgentManager:
    def __init__(self):
        # Load the model client from config
        with open("model_config.yml", "r") as f:
            model_config = yaml.safe_load(f)
        self.model_client = ChatCompletionClient.load_component(model_config)
        
        self.Enhancer_system_message = """
            You are an AI specializing in enhancing user requirements for UI design. Your task is to elaborate on the user's requirements in a detailed and comprehensive manner. 
            Ensure that the elaboration covers all aspects of UI design, including layout, color schemes, typography, and user experience. 
            The detailed requirements should be clear, actionable, and aligned with best practices in UI/UX design.
            If any image URLs are provided within the prompt, use the image URLs to display images on the UI as per user's requirement. 
            Note: Don't change the original UI requirement from the user. Keep in mind to not modify the original contents. 
        """
        self.CodeBuilder_system_message = """
            You are an AI specializing in building code. You need to generate HTML, CSS, and JavaScript scripts according to the user requirements. The generated script should be error-free, with errors handled within the script.
            The generated code should be well-documented, easy to understand, optimized for performance, and should not cause any memory leaks or performance issues. Generate the code in a single block, including HTML, CSS, and JavaScript.
            The generated code should be compatible with modern web standards and should work seamlessly across different browsers and devices. If user wants to generate any image, then generate the image using gpt 4o model and provide the image link in the code.
        """
        self.Evaluation_system_message = """
            You are an AI specializing in evaluating UI scripts. Your task is to review the HTML, CSS, and JavaScript code generated based on the user's requirements. 
            Confirm whether the generated code is perfect for rendering, ensuring it is error-free, optimized for performance, and adheres to best practices in UI/UX design. 
            Provide clear and concise feedback on any issues found and suggest improvements if necessary.
        """
        self.ImageGenerator_system_message = """
            You are an AI specializing in generating images based on user requirements. Your task is to create images that match the user's specifications and provide a link to the generated image.
            Collect the image requirements from the Enhancer agent and ensure that the generated image matches those specifications.
        """
        # Initialize agents with the model client and system messages
        # Agent-1: Enhancer agent
        self.Enhancer_agent = AssistantAgent(
            name="Enhancer_agent",
            model_client=self.model_client,
            system_message=self.Enhancer_system_message,
        )

        # Agent-2: CodeBuilder agent    
        self.CodeBuilder_agent = AssistantAgent(
            name="CodeBuilder_agent",
            model_client=self.model_client,
            system_message=self.CodeBuilder_system_message,
        )

        # Agent-3: Evaluation agent
        self.Evaluation_agent = AssistantAgent(
            name="Evaluation_agent",
            model_client=self.model_client,
            system_message=self.Evaluation_system_message,
        )

        # Agent-4: ImageGenerator agent
        self.ImageGenerator_agent = AssistantAgent(
            name="ImageGenerator_agent",
            model_client=self.model_client,
            system_message=self.ImageGenerator_system_message,
        )

    async def start_multi_agentic_chat(self, prompt: str) -> str:
        final_user_prompt = f"""
        {prompt}\n 
        Please provide a detailed description of the UI requirements.
        """
        # Create a text message with the user prompt
        Enhancer_agent_response = await self.Enhancer_agent.on_messages(
            [TextMessage(content=final_user_prompt, source="user")],
            CancellationToken(),
        )
        
        # Check if the user specified to add any images
        if "image" in prompt.lower():
            ImageGenerator_agent_response = await self.ImageGenerator_agent.on_messages(
                [TextMessage(content=Enhancer_agent_response.chat_message.content, source="Enhancer_agent")],
                CancellationToken(),
            )
            image_prompt = ImageGenerator_agent_response.chat_message.content
            image_response = requests.post(
                "https://cmo-compliance-hyc7gzhqdsb4e5bg.eastus-01.azurewebsites.net/image/generate",
                json={
                    "prompt": image_prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "standard",
                    "style": "vivid",
                    "response_format": "url"
                }
            )
            image_link = image_response.json()[0]
            enhanced_content_with_image = f'{Enhancer_agent_response.chat_message.content}\n<img src="{image_link}" alt="Generated Image">'
        else:
            enhanced_content_with_image = Enhancer_agent_response.chat_message.content

        # Agent-2: CodeBuilder agent
        CodeBuilder_agent_response = await self.CodeBuilder_agent.on_messages(
            [TextMessage(content=enhanced_content_with_image, source="Enhancer_agent")],
            CancellationToken(),
        )

        # Agent-3: Evaluation agent
        Evaluation_agent_prompt = f"""
        The detailed UI requirements provided by the Enhancer agent are as follows:
        {enhanced_content_with_image}
        
        Based on these requirements, the CodeBuilder agent has generated the following code:
        {CodeBuilder_agent_response.chat_message.content}
        
        Please review the generated code for compliance with UI/UX best practices and provide feedback.
        """
        
        Evaluation_agent_response = await self.Evaluation_agent.on_messages(
            [TextMessage(content=Evaluation_agent_prompt, source="CodeBuilder_agent")],
            CancellationToken(),
        )
        
        conversation_log = [
            {
                "agent": "Enhancer Agent", 
                "message": "Detailed UI requirements:\n" + enhanced_content_with_image
            },
            {
                "agent": "CodeBuilder Agent", 
                "message": "Generated code based on the UI requirements:\n" + CodeBuilder_agent_response.chat_message.content
            },
            {
                "agent": "Evaluation Agent", 
                "message": "Feedback on the generated code:\n" + Evaluation_agent_response.chat_message.content
            }
        ]
        
        return (CodeBuilder_agent_response.chat_message.content, Evaluation_agent_response.chat_message.content), conversation_log

    
    async def updated_multi_agentic_chat(self, prompt: str) -> str:
        final_user_prompt = f"""
        {prompt}\n 
        Please provide a detailed description of the UI requirements.
        """
        # Create a text message with the user prompt
        Enhancer_agent_response = await self.Enhancer_agent.on_messages(
            [TextMessage(content=final_user_prompt, source="user")],
            CancellationToken(),
        )
        
        # Check if the user specified to add any images
        # if "image" in prompt.lower():
        #     ImageGenerator_agent_response = await self.ImageGenerator_agent.on_messages(
        #         [TextMessage(content=Enhancer_agent_response.chat_message.content, source="Enhancer_agent")],
        #         CancellationToken(),
        #     )
        #     image_prompt = ImageGenerator_agent_response.chat_message.content
        #     image_response = requests.post(
        #         "https://cmo-compliance-hyc7gzhqdsb4e5bg.eastus-01.azurewebsites.net/image/generate",
        #         json={
        #             "prompt": image_prompt,
        #             "n": 1,
        #             "size": "1024x1024",
        #             "quality": "standard",
        #             "style": "vivid",
        #             "response_format": "url"
        #         }
        #     )
        #     image_link = image_response.json()[0]
        #     enhanced_content_with_image = f'{Enhancer_agent_response.chat_message.content}\n<img src="{image_link}" alt="Generated Image">'
        # else:
        #     enhanced_content_with_image = Enhancer_agent_response.chat_message.content

        # Agent-2: CodeBuilder agent
        CodeBuilder_agent_response = await self.CodeBuilder_agent.on_messages(
            [TextMessage(content=Enhancer_agent_response.chat_message.content, source="Enhancer_agent")],
            CancellationToken(),
        )

        # Agent-3: Evaluation agent
        # Evaluation_agent_prompt = f"""
        # The detailed UI requirements provided by the Enhancer agent are as follows:
        # {Enhancer_agent_response.chat_message.content}
        
        # Based on these requirements, the CodeBuilder agent has generated the following code:
        # {CodeBuilder_agent_response.chat_message.content}
        
        # Please review the generated code for compliance with UI/UX best practices and provide feedback.
        # """
        
        # Evaluation_agent_response = await self.Evaluation_agent.on_messages(
        #     [TextMessage(content=Evaluation_agent_prompt, source="CodeBuilder_agent")],
        #     CancellationToken(),
        # )
        
        conversation_log = [
            {
                "agent": "Enhancer Agent", 
                "message": "Detailed UI requirements:\n" + Enhancer_agent_response.chat_message.content
            },
            {
                "agent": "CodeBuilder Agent", 
                "message": "Generated code based on the UI requirements:\n" + CodeBuilder_agent_response.chat_message.content
            },
            # {
            #     "agent": "Evaluation Agent", 
            #     "message": "Feedback on the generated code:\n" + Evaluation_agent_response.chat_message.content
            # }
        ]
        
        return (CodeBuilder_agent_response.chat_message.content), conversation_log
    
    
    async def feedback_multi_agentic_chat(self, prompt: str) -> str:
        final_user_prompt = f"""
        {prompt}\n 
        Please provide a detailed description of the UI requirements.
        """
        
        CodeBuilder_agent_response = await self.CodeBuilder_agent.on_messages(
            [TextMessage(content=final_user_prompt, source="Enhancer_agent")],
            CancellationToken(),
        )
        
        conversation_log = [
            # {
            #     "agent": "Enhancer Agent", 
            #     "message": "Detailed UI requirements:\n" + Enhancer_agent_response.chat_message.content
            # },
            {
                "agent": "CodeBuilder Agent", 
                "message": "Generated code based on the UI requirements:\n" + CodeBuilder_agent_response.chat_message.content
            },
            # {
            #     "agent": "Evaluation Agent", 
            #     "message": "Feedback on the generated code:\n" + Evaluation_agent_response.chat_message.content
            # }
        ]
        
        return (CodeBuilder_agent_response.chat_message.content), conversation_log(antenv)