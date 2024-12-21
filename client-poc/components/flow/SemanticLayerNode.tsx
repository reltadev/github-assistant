import React from 'react'
import { Handle, Position } from 'reactflow'
import { LayersIcon } from 'lucide-react'

export function SemanticLayerNode({ data }: { data: { label: string } }) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-purple-200 w-64">
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <div className="flex items-center justify-center">
        <LayersIcon className="mr-2" />
        <div className="text-sm font-bold">{data.label}</div>
      </div>
    </div>
  )
}

