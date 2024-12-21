import React from 'react'
import { Handle, Position } from 'reactflow'
import { SearchIcon } from 'lucide-react'

export function QueryNode({ data }: { data: { label: string } }) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-yellow-200 w-64">
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center justify-center">
        <SearchIcon className="mr-2" />
        <div className="text-sm font-bold">{data.label}</div>
      </div>
    </div>
  )
}

