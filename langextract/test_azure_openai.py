#!/usr/bin/env python3
"""Test script for Azure OpenAI provider."""

import os
import sys
from typing import List

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add the langextract directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langextract'))

from langextract.providers.azure_openai import AzureOpenAILanguageModel
from langextract.core.data import FormatType


def test_azure_openai_basic():
    """Test basic Azure OpenAI functionality."""
    print("Testing Azure OpenAI provider...")
    
    # Test with environment variables from .env
    try:
        model = AzureOpenAILanguageModel(
            model_id='gpt-5-nano',
            deployment_name='gpt-5-nano-sf',  # Use the deployment name from the examples
            format_type=FormatType.JSON
        )
        
        print(f"✓ Model initialized successfully")
        print(f"  - Model ID: {model.model_id}")
        print(f"  - Deployment: {model.deployment_name}")
        print(f"  - Endpoint: {model.azure_endpoint}")
        print(f"  - API Version: {model.api_version}")
        
        # Test a simple prompt
        test_prompt = "What is the capital of France? Respond in JSON format with 'capital' and 'country' fields."
        
        print(f"\nTesting inference with prompt: {test_prompt}")
        
        results = list(model.infer([test_prompt]))
        
        if results:
            output = results[0][0]  # First result, first output
            print(f"✓ Inference successful")
            print(f"  - Score: {output.score}")
            print(f"  - Output: {output.output}")
        else:
            print("✗ No results returned")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True


def test_azure_openai_conversation():
    """Test Azure OpenAI with a multi-turn conversation."""
    print("\nTesting multi-turn conversation...")

    try:
        model = AzureOpenAILanguageModel(
            model_id='gpt-5-nano',
            deployment_name='gpt-5-nano-sf',
            format_type=FormatType.JSON
            # Note: gpt-5-nano only supports default temperature (1.0)
        )
        
        # Test conversation prompts
        prompts = [
            "I am going to Paris, what should I see? Respond in JSON format with a list of attractions.",
            "What is so great about the Eiffel Tower? Respond in JSON format with key points."
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}: {prompt}")
            results = list(model.infer([prompt]))
            
            if results:
                output = results[0][0]
                print(f"✓ Response {i} received")
                print(f"  - Output: {output.output[:200]}...")  # Show first 200 chars
            else:
                print(f"✗ No response for prompt {i}")
                
    except Exception as e:
        print(f"✗ Conversation test error: {e}")
        return False
    
    return True


def test_pattern_matching():
    """Test if Azure OpenAI patterns are working."""
    print("\nTesting pattern matching...")

    from langextract.providers import router
    from langextract.providers import load_builtins_once

    # Load built-in providers
    load_builtins_once()

    test_models = [
        'gpt-5-nano',
        'gpt-5-mini',
        'azure-gpt-4',
        'azure:gpt-5',
        'gpt-5-nano-sf'
    ]

    success_count = 0
    for model_name in test_models:
        try:
            provider_class = router.resolve(model_name)
            print(f"✓ {model_name} -> {provider_class.__name__}")
            success_count += 1
        except Exception as e:
            print(f"✗ {model_name} -> Error: {e}")

    return success_count == len(test_models)


def main():
    """Run all tests."""
    print("Azure OpenAI Provider Test Suite")
    print("=" * 40)
    
    # Check environment variables
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment.")
        return False
    
    print("✓ Environment variables found")
    
    # Run tests
    tests = [
        test_pattern_matching,
        test_azure_openai_basic,
        test_azure_openai_conversation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result if result is not None else False)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
