from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, BaseMessage
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory
from typing import List
import os

class TravelBot:

    CONVERSATION_PROMPT_TEMPLATE = ''' You are a helpful travel planning assistant.
        Your goal is to collect the user's name, phone number, destination,
        number of travelers, duration, starting city and travel dates.  Based on the user's input, determine what
        information is missing and ask the next relevant question.
        Starting city and destination is must.
        Travel dates are must to get any query related itinerary pricing or quotes.
        If all required information is provided, confirm that you have
        everything you need and summarize the information gathered.
        If the users ask for itinerary or price say that we are working
        on it and will reach you shortly. Response should not have any json,
        just return the text that I will be asking the user. '''

    SUMMARY_PROMPT_TEMPLATE = ''' Please extract the name, phone number, destination,
        number of travelers, duration, travel dates, duration and any additional requirements
        from the user in the attached json format
        {"name": null, "phone_number": null, "destination": null,
        "number_of_travelers": null, "travel_dates": null,
        "duration": null, "starting_city": null, summary: null}. Dont give me response
        in nested object. Need response strictly in the json format attached above only'''

    BOT_FIRST_MSSG = "How can I help you?"

    def __init__(self, user_id: str):
        # Load environment variables
        load_dotenv() # Will OPEN_API_KEY & PROJECT_ID

        # This is required to initialize firestore client to persist chat history
        gcp_project_id = os.getenv("PROJECT_ID")

        #Collection name for in the firestore DB
        self.collection_name = os.getenv("COLLECTION_NAME")

        # initize the model
        model = ChatOpenAI(model="gpt-4")
        self.conv_chain = model | StrOutputParser()

        #user_id is important as we are storing this as key where value is chat_history
        self.user_id = user_id

        # initialize the firestore client
        self.client = firestore.Client(project=gcp_project_id)
        self.chat_history_from_firestore = FirestoreChatMessageHistory(
            session_id=self.user_id,
            collection=self.collection_name,
            client=self.client,
        )

    def load_chat_history_from_firestore(self) -> List[BaseMessage]:
        
        #Loading the chat history from Firestore DB
        self.chat_history_from_firestore = FirestoreChatMessageHistory(
            session_id=self.user_id,
            collection=self.collection_name,
            client=self.client,
        )

        #If there is no history add the bot 1st message to be displayed for user
        if len(self.chat_history_from_firestore.messages) == 0:
            self.chat_history_from_firestore.add_ai_message(TravelBot.BOT_FIRST_MSSG)

        return self.chat_history_from_firestore.messages

    '''
        This is a private method and is called by class fuctions
        It prepares the prompt for the LLM
        arguments : 
            user_message : Last message from the user
            use_conversation_template : whether to use Summary or conversational template
    '''
    def __prepare_message_for_llm(self, user_message: str=None, 
                                  use_conversation_template: bool=True) -> List[BaseMessage]:

        #Get Chat history from firestore
        self.load_chat_history_from_firestore()

        #Add user_message 1st to the firestore and save it....
        if user_message != None:
            self.chat_history_from_firestore.add_user_message(user_message)

        # We are preparing the prompt for LLM which includes conversatonal or summary prompt 
        # and the chat history
        llm_chat_history = []
        conversation_system_message = None
        if use_conversation_template:
            conversation_system_message=SystemMessage(content=TravelBot.CONVERSATION_PROMPT_TEMPLATE)
        else:
            conversation_system_message=SystemMessage(content=TravelBot.SUMMARY_PROMPT_TEMPLATE)

        llm_chat_history.append(conversation_system_message)
        llm_chat_history.extend(self.chat_history_from_firestore.messages)

        return llm_chat_history
    
    '''
        Get the resposne from LLM for the given <user_message>
        It returns the whole chat history and not the latest repsonse
    '''
    def generate_ai_response(self, user_message: str) -> List[BaseMessage]:

        # Get Prompt
        llm_chat_history = self.__prepare_message_for_llm(user_message=user_message, 
                                                          use_conversation_template=True)
        
        # Call LLM for response
        response = self.conv_chain.invoke(llm_chat_history)

        # Persist LLM response in Firestore 1st and return whole chat history
        self.chat_history_from_firestore.add_ai_message(response)
        return self.chat_history_from_firestore.messages
    
    '''
        Generates summary of the chat conversation and return the same
        It doesn't takes any input
        Chat history is loaded from the Firestore DB
    '''
    def summarize_chat_history(self) -> str:

        llm_chat_history = self.__prepare_message_for_llm(use_conversation_template=False)
        response = self.conv_chain.invoke(llm_chat_history)
        return response