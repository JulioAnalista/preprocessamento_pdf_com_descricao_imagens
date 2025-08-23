# Copyright 2025 Google LLC.
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

"""Azure OpenAI provider for LangExtract."""
# pylint: disable=duplicate-code

from __future__ import annotations

import concurrent.futures
import dataclasses
import os
from typing import Any, Iterator, Sequence

from langextract.core import base_model
from langextract.core import data
from langextract.core import exceptions
from langextract.core import schema
from langextract.core import types as core_types
from langextract.providers import patterns
from langextract.providers import router


@router.register(
    *patterns.AZURE_OPENAI_PATTERNS,
    priority=patterns.AZURE_OPENAI_PRIORITY,
)
@dataclasses.dataclass(init=False)
class AzureOpenAILanguageModel(base_model.BaseLanguageModel):
  """Language model inference using Azure OpenAI's API with structured output."""

  model_id: str = 'gpt-5-nano'
  api_key: str | None = None
  azure_endpoint: str | None = None
  api_version: str = '2025-03-01-preview'
  deployment_name: str | None = None
  format_type: data.FormatType = data.FormatType.JSON
  temperature: float | None = None
  max_workers: int = 10
  _client: Any = dataclasses.field(default=None, repr=False, compare=False)
  _extra_kwargs: dict[str, Any] = dataclasses.field(
      default_factory=dict, repr=False, compare=False
  )

  @property
  def requires_fence_output(self) -> bool:
    """Azure OpenAI JSON mode returns raw JSON without fences."""
    if self.format_type == data.FormatType.JSON:
      return False
    return super().requires_fence_output

  def __init__(
      self,
      model_id: str = 'gpt-5-nano',
      api_key: str | None = None,
      azure_endpoint: str | None = None,
      api_version: str = '2025-03-01-preview',
      deployment_name: str | None = None,
      format_type: data.FormatType = data.FormatType.JSON,
      temperature: float | None = None,
      max_workers: int = 10,
      **kwargs,
  ) -> None:
    """Initialize the Azure OpenAI language model.

    Args:
      model_id: The Azure OpenAI model ID to use (e.g., 'gpt-5-nano', 'gpt-5-mini').
      api_key: API key for Azure OpenAI service.
      azure_endpoint: Azure OpenAI endpoint URL.
      api_version: Azure OpenAI API version.
      deployment_name: Azure deployment name (defaults to model_id).
      format_type: Output format (JSON or YAML).
      temperature: Sampling temperature.
      max_workers: Maximum number of parallel API calls.
      **kwargs: Ignored extra parameters so callers can pass a superset of
        arguments shared across back-ends without raising ``TypeError``.
    """
    # Lazy import: OpenAI package required
    try:
      # pylint: disable=import-outside-toplevel
      import openai
    except ImportError as e:
      raise exceptions.InferenceConfigError(
          'Azure OpenAI provider requires openai package. '
          'Install with: pip install langextract[openai]'
      ) from e

    self.model_id = model_id
    self.api_key = api_key or os.getenv('AZURE_OPENAI_API_KEY')
    self.azure_endpoint = azure_endpoint or os.getenv('AZURE_OPENAI_ENDPOINT')
    self.api_version = api_version or os.getenv('AZURE_OPENAI_API_VERSION', '2025-03-01-preview')
    self.deployment_name = deployment_name or model_id
    self.format_type = format_type
    self.temperature = temperature
    self.max_workers = max_workers

    if not self.api_key:
      raise exceptions.InferenceConfigError(
          'Azure OpenAI API key not provided. Set AZURE_OPENAI_API_KEY environment variable or pass api_key parameter.'
      )

    if not self.azure_endpoint:
      raise exceptions.InferenceConfigError(
          'Azure OpenAI endpoint not provided. Set AZURE_OPENAI_ENDPOINT environment variable or pass azure_endpoint parameter.'
      )

    # Initialize the Azure OpenAI client
    self._client = openai.AzureOpenAI(
        api_key=self.api_key,
        azure_endpoint=self.azure_endpoint,
        api_version=self.api_version,
    )

    super().__init__(
        constraint=schema.Constraint(constraint_type=schema.ConstraintType.NONE)
    )
    self._extra_kwargs = kwargs or {}

  def _process_single_prompt(
      self, prompt: str, config: dict
  ) -> core_types.ScoredOutput:
    """Process a single prompt and return a ScoredOutput."""
    try:
      system_message = ''
      if self.format_type == data.FormatType.JSON:
        system_message = (
            'You are a helpful assistant that responds in JSON format.'
        )
      elif self.format_type == data.FormatType.YAML:
        system_message = (
            'You are a helpful assistant that responds in YAML format.'
        )

      messages = [{'role': 'user', 'content': prompt}]
      if system_message:
        messages.insert(0, {'role': 'system', 'content': system_message})

      api_params = {
          'model': self.deployment_name,  # Use deployment name for Azure
          'messages': messages,
          'n': 1,
      }

      # Only set temperature if explicitly provided
      temp = config.get('temperature', self.temperature)
      if temp is not None:
        api_params['temperature'] = temp

      if self.format_type == data.FormatType.JSON:
        # Enables structured JSON output for compatible models
        api_params['response_format'] = {'type': 'json_object'}

      if (v := config.get('max_output_tokens')) is not None:
        api_params['max_completion_tokens'] = v  # Azure uses max_completion_tokens
      if (v := config.get('top_p')) is not None:
        api_params['top_p'] = v
      for key in [
          'frequency_penalty',
          'presence_penalty',
          'seed',
          'stop',
          'logprobs',
          'top_logprobs',
      ]:
        if (v := config.get(key)) is not None:
          api_params[key] = v

      response = self._client.chat.completions.create(**api_params)

      # Extract the response text using the v1.x response format
      output_text = response.choices[0].message.content

      return core_types.ScoredOutput(score=1.0, output=output_text)

    except Exception as e:
      raise exceptions.InferenceRuntimeError(
          f'Azure OpenAI API error: {str(e)}', original=e
      ) from e

  def infer(
      self, batch_prompts: Sequence[str], **kwargs
  ) -> Iterator[Sequence[core_types.ScoredOutput]]:
    """Runs inference on a list of prompts via Azure OpenAI's API.

    Args:
      batch_prompts: A list of string prompts.
      **kwargs: Additional generation params (temperature, top_p, etc.)

    Yields:
      Lists of ScoredOutputs.
    """
    merged_kwargs = self.merge_kwargs(kwargs)

    config = {}

    # Only add temperature if it's not None
    temp = merged_kwargs.get('temperature', self.temperature)
    if temp is not None:
      config['temperature'] = temp
    if 'max_output_tokens' in merged_kwargs:
      config['max_output_tokens'] = merged_kwargs['max_output_tokens']
    if 'top_p' in merged_kwargs:
      config['top_p'] = merged_kwargs['top_p']

    # Forward Azure OpenAI-specific parameters
    for key in [
        'frequency_penalty',
        'presence_penalty',
        'seed',
        'stop',
        'logprobs',
        'top_logprobs',
    ]:
      if key in merged_kwargs:
        config[key] = merged_kwargs[key]

    # Use parallel processing for batches larger than 1
    if len(batch_prompts) > 1 and self.max_workers > 1:
      with concurrent.futures.ThreadPoolExecutor(
          max_workers=min(self.max_workers, len(batch_prompts))
      ) as executor:
        future_to_index = {
            executor.submit(
                self._process_single_prompt, prompt, config.copy()
            ): i
            for i, prompt in enumerate(batch_prompts)
        }

        results: list[core_types.ScoredOutput | None] = [None] * len(
            batch_prompts
        )
        for future in concurrent.futures.as_completed(future_to_index):
          index = future_to_index[future]
          try:
            results[index] = future.result()
          except Exception as e:
            raise exceptions.InferenceRuntimeError(
                f'Parallel inference error: {str(e)}', original=e
            ) from e

        for result in results:
          if result is None:
            raise exceptions.InferenceRuntimeError(
                'Failed to process one or more prompts'
            )
          yield [result]
    else:
      # Sequential processing for single prompt or worker
      for prompt in batch_prompts:
        result = self._process_single_prompt(prompt, config.copy())
        yield [result]  # pylint: disable=duplicate-code
