from pprint import pprint
from langchain.chains import LLMChain
from prompts import *


classifier = LLMChain(prompt=classification_prompt, output_key='classification')
constraints_extractor = LLMChain(prompt=constraints_extraction_prompt, output_key='constraints')

if __name__=="__main__":


