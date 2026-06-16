export interface VisionModel {
  id: string
  label: string
  free: boolean
}

export const VISION_MODELS: VisionModel[] = [
  { id: 'google/gemma-4-31b-it:free', label: 'Gemma 4 31B (free — default)', free: true },
  { id: 'openrouter/free', label: 'OpenRouter Free Router (auto)', free: true },
  { id: 'google/gemma-4-26b-a4b-it:free', label: 'Gemma 4 26B (free)', free: true },
  { id: 'google/gemma-4-31b-it:free', label: 'Gemma 4 31B (free)', free: true },
  { id: 'nvidia/nemotron-nano-12b-v2-vl:free', label: 'Nemotron Nano 12B VL (free)', free: true },
  { id: 'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free', label: 'Nemotron 3 Nano Omni (free)', free: true },
  { id: 'google/gemma-3-12b-it', label: 'Gemma 3 12B (paid)', free: false },
  { id: 'openai/gpt-4o-mini', label: 'GPT-4o Mini (paid)', free: false },
]
