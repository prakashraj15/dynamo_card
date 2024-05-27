from langchain_community.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_vertexai import VertexAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from vertexai.generative_models import GenerativeModel
from langchain_core.output_parsers import JsonOutputParser
import json
from tqdm import tqdm

import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiProcessor:

    def __init__(self, model_name, project, location):
        self.model = VertexAI(model_name=model_name, project=project, location=location)
          
    def generate_document_summary(self, documents: list, **args):
        chain_type = "map_reduce" if len(documents) > 1 else "stuff"

        chain = load_summarize_chain(llm = self.model, chain_type = chain_type, **args)

        return chain.run(documents)
    
    def count_total_tokens(self, documents: list):
        temp_model = GenerativeModel("gemini-1.0-pro")
        total_tokens = 0
        logger.info("Counting total billable characters....")
        for doc in tqdm(documents):
            total_tokens += temp_model.count_tokens(doc.page_content).total_billable_characters
        return total_tokens

    
    def get_model(self):
        return self.model
    



class YoutubeProcessor:

    def __init__(self, genai_processor: GeminiProcessor):
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.GeminiProcessor = genai_processor


    def retrieve_text(self, video_url: str, verbose = True):
        loader = YoutubeLoader.from_youtube_url(video_url, add_video_info=True)
        docs  = loader.load()
        result = self.text_splitter.split_documents(docs)

        author = result[0].metadata['author']
        length = result[0].metadata['length']
        title = result[0].metadata['title']
        total_size = len(result)
        total_billable_characters = self.GeminiProcessor.count_total_tokens(result)

        if verbose:
            logger.info(f"{author}\n{length}\n{title}\n{total_size}\n{total_billable_characters}")

        return result
    
    def find_key_concepts(self, documents: list, group_size: int=2, verbose = False):
        if group_size > len(documents):
            raise ValueError("Group size is larger than the number of documents")
        
        # if group_size == 0:
        #     group_size = len(documents) // 5
        #     if verbose:
        #         logger.info(f"Group size is not specified. Group size is set to {group_size}")
        
        num_docs_per_group = len(documents) // group_size + (len(documents) % group_size > 0)

        # if num_docs_per_group >=10:
        #     raise ValueError("Each group has more than 10 documents and output quality will be degraded significantly. Decrease the group_size parameter to reduce the number of documents per group.")
        # elif num_docs_per_group > 5:
        #     logger.warning("Each group has more than 5 documents. The output quality may be degraded. Consider increasing the group_size parameter to reduce the number of documents per group.")

        groups = [documents[i:i + num_docs_per_group] for i in range(0, len(documents), num_docs_per_group)]

        batch_concepts = []
        batch_cost = 0

        logger.info("Finding key concepts....")

        for group in tqdm(groups):

            group_content = ""

            for doc in group:
                group_content += doc.page_content

            prompt = PromptTemplate(
                template="""
                Find and define key concepts or terms found in the text:
                {text}
                
                Respond in the following format as a JSON object without any backticks separating each concept 
                with a comma and dont give any whitespace:
                {{"concept": "definition", "concept": "definition", "concept": "definition",...}}
                """,
                input_variables=["text"]
            )

            parser = JsonOutputParser()

            chain = prompt | self.GeminiProcessor.model| parser

            output_concept = chain.invoke({"text": group_content})
            batch_concepts.append(output_concept)
            if verbose:
                total_input_char = len(group_content)
                total_input_cost = (total_input_char/1000)*0.000125
                logger.info(f"Running chain on {len(group)} documents")
                logger.info(f"Total input characters: {total_input_char}")
                logger.info(f"Total input cost: {total_input_cost}")
                total_output_char = len(output_concept)
                total_output_cost = (total_output_char/1000)*0.000375
                logger.info(f"Total output characters: {total_output_char}")
                logger.info(f"Total output cost: {total_output_cost}")
                batch_cost += total_input_cost + total_output_cost
                logger.info(f"Total group cost: {total_input_cost + total_output_cost}")
            
        # processed_concepts = [json.loads(concept) for concept in batch_concepts]
        # json_output = json.dumps(processed_concepts, indent=4)
        # processed_concepts = []
        # for concepts in batch_concepts:
        #     processed_concept = json.loads(concepts)
        #     print(processed_concept)
        #     processed_concepts.append(processed_concept)

        logger.info(f"Total analysis cost: $ {batch_cost}")
        return batch_concepts
    


