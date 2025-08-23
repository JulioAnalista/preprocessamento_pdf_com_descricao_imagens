#!/usr/bin/env python3
"""Example of using LangExtract with Azure OpenAI for structured data extraction."""

import os
from dotenv import load_dotenv
from typing import List, Optional
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

import langextract


# Define data models for extraction
class Person(BaseModel):
    """A person mentioned in the text."""
    name: str = Field(description="Full name of the person")
    age: Optional[int] = Field(description="Age if mentioned", default=None)
    occupation: Optional[str] = Field(description="Job or profession if mentioned", default=None)
    location: Optional[str] = Field(description="Location or city if mentioned", default=None)


class Company(BaseModel):
    """A company mentioned in the text."""
    name: str = Field(description="Company name")
    industry: Optional[str] = Field(description="Industry or sector", default=None)
    location: Optional[str] = Field(description="Company location", default=None)
    founded: Optional[int] = Field(description="Year founded if mentioned", default=None)


class NewsArticle(BaseModel):
    """Structured representation of a news article."""
    title: str = Field(description="Article title or main topic")
    summary: str = Field(description="Brief summary of the article")
    people: List[Person] = Field(description="People mentioned in the article", default_factory=list)
    companies: List[Company] = Field(description="Companies mentioned in the article", default_factory=list)
    key_facts: List[str] = Field(description="Important facts or events", default_factory=list)
    sentiment: str = Field(description="Overall sentiment: positive, negative, or neutral")


def test_azure_openai_extraction():
    """Test Azure OpenAI with structured data extraction."""
    print("Testing Azure OpenAI with LangExtract for structured data extraction")
    print("=" * 70)

    # Sample text for extraction
    sample_text = """
    Microsoft CEO Satya Nadella announced today that the company will invest $10 billion
    in artificial intelligence research over the next five years. The 56-year-old executive,
    who has led Microsoft since 2014, made the announcement at the company's headquarters
    in Redmond, Washington.

    The investment will focus on developing new AI models and expanding Microsoft's
    partnership with OpenAI, the San Francisco-based startup founded in 2015.
    OpenAI's CEO Sam Altman, 38, expressed enthusiasm about the collaboration,
    stating it will accelerate the development of artificial general intelligence.

    This move positions Microsoft as a major player in the AI race, competing directly
    with Google's parent company Alphabet and Amazon. Industry analysts view this as
    a positive development for the technology sector, though some express concerns
    about the rapid pace of AI advancement.
    """

    try:
        # Extract structured data using Azure OpenAI
        print("Extracting structured data from sample text...")
        print(f"Text length: {len(sample_text)} characters")
        print()

        # Define extraction prompt and examples
        prompt = """Extract structured information from the news article including:
        - People mentioned (name, age, occupation, location)
        - Companies mentioned (name, industry, location, founded year)
        - Key facts and events
        - Overall sentiment"""

        examples = [
            langextract.data.ExampleData(
                text="Apple CEO Tim Cook, 62, announced record revenue at the company's Cupertino headquarters.",
                extractions=[
                    langextract.data.Extraction(
                        extraction_class="news_article",
                        extraction_text="Apple CEO Tim Cook, 62, announced record revenue at the company's Cupertino headquarters.",
                        attributes={
                            "people": [{"name": "Tim Cook", "age": 62, "occupation": "CEO", "location": "Cupertino"}],
                            "companies": [{"name": "Apple", "location": "Cupertino"}],
                            "key_facts": ["Record revenue announced"],
                            "sentiment": "positive"
                        }
                    )
                ]
            )
        ]

        # Use Azure OpenAI model
        results = langextract.extract(
            text_or_documents=sample_text,
            prompt_description=prompt,
            examples=examples,
            model_id='gpt-5-nano',  # This will use our Azure OpenAI provider
        )
        
        print("✓ Extraction successful!")
        print()

        # Display results
        if results.extractions:
            print(f"Found {len(results.extractions)} extraction(s):")
            for i, extraction in enumerate(results.extractions, 1):
                print(f"\nExtraction {i}:")
                print(f"  Class: {extraction.extraction_class}")
                print(f"  Text: {extraction.extraction_text[:100]}...")
                print(f"  Attributes: {extraction.attributes}")
        else:
            print("No extractions found")

        return True
        
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return False


def test_batch_extraction():
    """Test batch extraction with multiple texts."""
    print("\n" + "=" * 70)
    print("Testing batch extraction with Azure OpenAI")
    print("=" * 70)

    # Multiple sample texts
    texts = [
        "Apple Inc. reported record quarterly revenue of $123 billion. CEO Tim Cook, 62, praised the strong performance of iPhone sales in China.",
        "Tesla's stock price surged 15% after Elon Musk announced plans to expand production in Berlin. The 52-year-old entrepreneur expects to double output by 2025.",
        "Amazon founder Jeff Bezos stepped down as CEO last year, passing leadership to Andy Jassy. The Seattle-based company continues to dominate e-commerce."
    ]

    try:
        print(f"Processing {len(texts)} texts...")

        # Simple extraction prompt
        prompt = "Extract company names, people names, and key business information from the text."

        examples = [
            langextract.data.ExampleData(
                text="Microsoft CEO Satya Nadella announced new AI investments.",
                extractions=[
                    langextract.data.Extraction(
                        extraction_class="business_info",
                        extraction_text="Microsoft CEO Satya Nadella announced new AI investments.",
                        attributes={
                            "companies": ["Microsoft"],
                            "people": ["Satya Nadella"],
                            "key_info": ["AI investments announced"]
                        }
                    )
                ]
            )
        ]

        # Batch extraction
        results = langextract.extract(
            text_or_documents=texts,
            prompt_description=prompt,
            examples=examples,
            model_id='gpt-5-nano',
        )

        print("✓ Batch extraction successful!")
        print()

        if results.extractions:
            print(f"Found {len(results.extractions)} total extraction(s):")
            for i, extraction in enumerate(results.extractions, 1):
                print(f"\nExtraction {i}:")
                print(f"  Text: {extraction.extraction_text[:80]}...")
                print(f"  Attributes: {extraction.attributes}")
        else:
            print("No extractions found")

        return True

    except Exception as e:
        print(f"✗ Batch extraction failed: {e}")
        return False


def test_different_models():
    """Test different Azure OpenAI models."""
    print("\n" + "=" * 70)
    print("Testing different Azure OpenAI models")
    print("=" * 70)

    text = "Microsoft announced a new AI partnership with OpenAI in Redmond, Washington."

    # Simple extraction prompt
    prompt = "Extract the main topic and key entities (companies, locations) from the text."

    examples = [
        langextract.data.ExampleData(
            text="Google launched a new product in Mountain View, California.",
            extractions=[
                langextract.data.Extraction(
                    extraction_class="simple_info",
                    extraction_text="Google launched a new product in Mountain View, California.",
                    attributes={
                        "main_topic": "Product launch",
                        "key_entities": ["Google", "Mountain View", "California"]
                    }
                )
            ]
        )
    ]

    # Test different model patterns that should resolve to Azure OpenAI
    models_to_test = [
        'gpt-5-nano',
        'gpt-5-mini',
        'azure-gpt-4',
        'azure:gpt-5'
    ]

    results = []
    for model in models_to_test:
        try:
            print(f"Testing model: {model}")
            result = langextract.extract(
                text_or_documents=text,
                prompt_description=prompt,
                examples=examples,
                model_id=model,
            )
            if result.extractions:
                main_topic = result.extractions[0].attributes.get('main_topic', 'Unknown')
                print(f"✓ {model}: {main_topic}")
                results.append(True)
            else:
                print(f"✗ {model}: No extractions found")
                results.append(False)
        except Exception as e:
            print(f"✗ {model}: {e}")
            results.append(False)

    return all(results)


def main():
    """Run all examples."""
    print("Azure OpenAI LangExtract Examples")
    print("=" * 70)
    
    # Check environment variables
    required_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"✗ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment.")
        return False
    
    print("✓ Environment variables found")
    print(f"  Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"  API Version: {os.getenv('AZURE_OPENAI_API_VERSION', '2025-03-01-preview')}")
    print()
    
    # Run examples
    examples = [
        test_azure_openai_extraction,
        test_batch_extraction,
        test_different_models,
    ]
    
    results = []
    for example in examples:
        try:
            result = example()
            results.append(result)
        except Exception as e:
            print(f"✗ Example {example.__name__} failed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 70)
    print("Example Summary:")
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All examples completed successfully!")
        return True
    else:
        print("✗ Some examples failed.")
        return False


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
