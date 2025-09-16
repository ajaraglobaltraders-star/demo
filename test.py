"""
SOW Narrator - SIMPLE HARDCODED VERSION
Just change the CLIENT_ID below and run!
"""

import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sow_class import SOW
from utils.logger_utils import get_logger
from utils.utils_main import process_client_sow_from_end_to_end
from utils.utils_common import get_properties_from_file, read_yaml_file
from config.constants import MESSAGE_SUB_CLASSIFICATIONS

# =============================================================================
# HARDCODED SETTINGS - CHANGE THESE AS NEEDED
# =============================================================================
CLIENT_ID = 1716338600  # <-- CHANGE THIS TO YOUR CLIENT ID
SCENARIO = None  # <-- Optional: "employment_income", "business_ownership", etc.
DOCUMENT_UNIVERSAL_KEY = None  # <-- Optional: specific document key

# Environment settings
CRDB_ENV = "QA"
OPENAI_ENV = "TEST"
GENESIS_ENV = "TEST"
CREDENTIALS_FROM_ENV_VAR = 0  # Set to 1 if using environment variables

# Paths
DATA_DIR = "D:/projects/NEW_SYNE_WMA/SOW/src/data"
CONFIG_REF_DATA_ROOT_PATH = "./"
CRDB_API_CA_CERT_FILE = "~/.secure/crdb/qa/1-TEST-SHA2.pem"
CRDB_API_CERT_FILE = "~/.secure/crdb/qa/FA0IIJF.crt"
CRDB_API_KEY_FILE = "~/.secure/crdb/qa/FA0IIJF.key"
# =============================================================================


def sow_narrator(client_id: int, args_dict: Dict[str, Any], 
                db_settings: Dict[str, Any], scenario: Optional[str] = None,
                document_universal_key: Optional[str] = None,
                conn=None, logger=None) -> Dict[str, Any]:
    """
    Generate SOW narrative for a client using your existing infrastructure.
    """
    logger = logger or get_logger("SOW_NARRATOR")
    logger.info(f"Starting SOW narrative generation for client: {client_id}")
    
    try:
        # Step 1: Initialize your existing SOW class
        sow_obj = SOW(args=args_dict, db_settings=db_settings, conn=conn)
        
        # Step 2: Use your existing process_client_sow_from_end_to_end function
        existing_result = process_client_sow_from_end_to_end(
            client_id=client_id,
            docs_metadata_api_obj=sow_obj.docs_metadata_api_obj,
            db_obj=sow_obj.db_obj,
            db_schema=sow_obj.db_schema,
            crdb_api_obj=sow_obj.crdb_api_obj,
            data_dir=sow_obj.sow_args.data_dir,
            prompt_dir=sow_obj.sow_args.config_ref_data_root_path,
            document_client=sow_obj.document_client,
            openai_client=sow_obj.openai_client,
            message_sub_classifications=MESSAGE_SUB_CLASSIFICATIONS,
            logger=logger,
            time_created=datetime.now(),
            document_universal_key=document_universal_key,
            sow_scenario=scenario,
            enable_document_process=sow_obj.sow_args.enable_document_process,
            use_existing_sow=sow_obj.sow_args.use_existing_sow,
            add_ocr_tables=sow_obj.sow_args.add_ocr_tables
        )
        
        if not existing_result:
            return {
                "client_id": client_id,
                "status": "error",
                "error_message": "Failed to process client SOW using existing function",
                "original_narrative": "",
                "enhanced_narrative": ""
            }
        
        # Step 3: Extract the narrative from the existing result
        existing_narrative = _extract_narrative_from_result(existing_result)
        
        # Step 4: Enhance the narrative using LLM (NEW PART)
        enhanced_narrative = _enhance_narrative_with_llm(
            existing_narrative, client_id, scenario, sow_obj.openai_client, logger
        )
        
        # Step 5: Create result
        result = {
            "client_id": client_id,
            "generation_timestamp": datetime.now(),
            "original_narrative": existing_narrative,
            "enhanced_narrative": enhanced_narrative,
            "status": "success"
        }
        
        logger.info(f"SOW narrative generation completed for client: {client_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating SOW narrative for client {client_id}: {str(e)}")
        return {
            "client_id": client_id,
            "generation_timestamp": datetime.now(),
            "status": "error",
            "error_message": str(e),
            "original_narrative": "",
            "enhanced_narrative": ""
        }


def _extract_narrative_from_result(existing_result: Dict[str, Any]) -> str:
    """Extract narrative from the existing result."""
    try:
        if isinstance(existing_result, dict):
            narrative = (existing_result.get('narrative') or 
                       existing_result.get('final_narrative') or 
                       existing_result.get('sow_narrative') or 
                       existing_result.get('generated_narrative', ''))
            return narrative
        elif isinstance(existing_result, str):
            return existing_result
        else:
            return str(existing_result)
    except Exception:
        return ""


def _enhance_narrative_with_llm(existing_narrative: str, client_id: int, 
                              scenario: Optional[str], openai_client, logger) -> str:
    """Enhance the existing narrative using LLM (NEW PART)."""
    try:
        if not existing_narrative or existing_narrative.strip() == "":
            return "No narrative available to enhance."
        
        enhancement_prompt = f"""
You are an expert at enhancing and refining SOW narratives for financial institutions.
Take the following narrative and improve it for clarity, professionalism, and compliance.

Client ID: {client_id}
Scenario Focus: {scenario or 'General SOW narrative'}

Original Narrative:
{existing_narrative}

Instructions:
1. Improve clarity and flow
2. Ensure professional tone
3. Fix any grammatical issues
4. Maintain all factual information
5. Make it more suitable for regulatory compliance
6. Keep the same structure but enhance the language
7. If the narrative is already good, make minor improvements only

Enhanced Narrative:
"""
        
        enhanced = openai_client.execute_prompt(enhancement_prompt)
        return enhanced.strip()
        
    except Exception as e:
        logger.error(f"Error enhancing narrative with LLM: {str(e)}")
        return existing_narrative


if __name__ == "__main__":
    # Build args_dict from hardcoded settings
    args_dict = {
        "data_dir": DATA_DIR,
        "config_ref_data_root_path": CONFIG_REF_DATA_ROOT_PATH,
        "crdb_api_ca_cert_file": CRDB_API_CA_CERT_FILE,
        "crdb_api_cert_file": CRDB_API_CERT_FILE,
        "crdb_api_key_file": CRDB_API_KEY_FILE,
        "credentials_from_env_var": CREDENTIALS_FROM_ENV_VAR,
        "save_output_to_db": 0,
        "client_identifier": CLIENT_ID,
        "document_universal_key": DOCUMENT_UNIVERSAL_KEY,
        "sow_scenario": SCENARIO,
        "openai_env": OPENAI_ENV,
        "crdb_env": CRDB_ENV,
        "genesis_env": GENESIS_ENV,
        "update_status_table": 0
    }
    
    # Load credentials and database settings
    sow_credentials = get_properties_from_file(
        "~/.secure/crdb/staat_sow_credentials.properties")
    db_config = read_yaml_file(
        os.path.join(CONFIG_REF_DATA_ROOT_PATH, "config/db_settings.yml"))
    db_config = db_config[GENESIS_ENV]
    db_instance = db_config['db_instance']

    # Set up database settings and API keys
    if CREDENTIALS_FROM_ENV_VAR:
        db_settings = {
            "host": os.getenv("GP_HOST"),
            "db": os.getenv("GP_DB"),
            "port": "5432",
            "user": os.getenv("GP_USERNAME"),
            "password": os.getenv("GP_PASSWORD"),
        }
        crdb_api_key = os.getenv(f"CRDB_API_KEY_{CRDB_ENV}")
        azure_document_service_api_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        openai_api_key = os.getenv(f"OPENAI_API_KEY_{OPENAI_ENV}")
    else:
        db_settings = {
            "host": sow_credentials[f'gp_host_{db_instance}'],
            "db": sow_credentials[f'gp_db_{db_instance}'],
            "port": sow_credentials[f'gp_port_{db_instance}'],
            "user": sow_credentials[f'gp_user_{db_instance}'],
            "password": sow_credentials[f'gp_password_{db_instance}'],
        }
        crdb_api_key = sow_credentials[f"crdb_api_key_{CRDB_ENV.lower()}"]
        azure_document_service_api_key = sow_credentials["document intelligence api key"]
        openai_api_key = sow_credentials[f"openai_api_key_{OPENAI_ENV.lower()}"]

    # Update args_dict with API keys
    args_dict.update({
        "azure_document_service_api_key": azure_document_service_api_key,
        "openai_api_key": openai_api_key,
        "crdb_api_key": crdb_api_key,
        "token_client_id": "",
        "token_client_secret": ""
    })

    print(f"Starting SOW Narrator for Client ID: {CLIENT_ID}")
    print(f"Scenario: {SCENARIO or 'General'}")
    print(f"Document Key: {DOCUMENT_UNIVERSAL_KEY or 'All documents'}")
    print("=" * 50)

    # Call the main function
    result = sow_narrator(
        client_id=CLIENT_ID,
        args_dict=args_dict,
        db_settings=db_settings,
        scenario=SCENARIO,
        document_universal_key=DOCUMENT_UNIVERSAL_KEY
    )

    # Display results
    print(f"\nStatus: {result['status']}")
    if result['status'] == 'success':
        print(f"\nOriginal Narrative:")
        print("-" * 30)
        print(result['original_narrative'])
        print(f"\nEnhanced Narrative:")
        print("-" * 30)
        print(result['enhanced_narrative'])
    else:
        print(f"Error: {result['error_message']}")
