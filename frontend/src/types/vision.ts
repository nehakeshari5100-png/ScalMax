// TypeScript types for Gemma Vision Analysis Engine

export interface ChartAnalysisResult {
  trend: string
  marketStructure: string
  liquidity: string
  supportZones: string[]
  resistanceZones: string[]
  entryIdeas: string[]
  riskZones: string[]
  confidence: number
}

export interface VisionAnalysisResponse {
  success: boolean
  data: ChartAnalysisResult | null
  raw: string | null
  model: string
  error: string | null
}

export interface VisionModel {
  id: string
  name: string
  description: string
  default: boolean
}

export interface VisionModelsResponse {
  models: VisionModel[]
}
