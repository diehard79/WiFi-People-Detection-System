'use client'

import { useState } from 'react'

interface WallHeatmapProps {
  probabilities: number[][] | null
  loading?: boolean
}

export function WallHeatmap({ probabilities, loading = false }: WallHeatmapProps) {
  const [selectedCell, setSelectedCell] = useState<{ row: number; col: number } | null>(null)

  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading heatmap...</p>
          </div>
        </div>
      </div>
    )
  }

  if (!probabilities || probabilities.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="text-6xl mb-4">🌡️</div>
            <p className="text-gray-600">No heatmap data available</p>
            <p className="text-sm text-gray-500 mt-2">Run detection to generate wall probabilities</p>
          </div>
        </div>
      </div>
    )
  }

  const rows = probabilities.length
  const cols = probabilities[0].length

  // Get color for probability value
  const getColor = (value: number) => {
    // Blue (low) -> Red (high)
    const hue = (1 - value) * 240 // 240 = blue, 0 = red
    return `hsl(${hue}, 70%, 50%)`
  }

  const handleCellClick = (row: number, col: number) => {
    setSelectedCell({ row, col })
  }

  const handleCellMouseEnter = (row: number, col: number) => {
    setSelectedCell({ row, col })
  }

  const handleCellMouseLeave = () => {
    setSelectedCell(null)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Wall Detection Heatmap</h2>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Heatmap Grid */}
        <div className="flex-1">
          <div className="inline-block">
            <div
              className="grid gap-1 border-2 border-gray-300 rounded-lg p-2 bg-gray-50"
              style={{
                gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
              }}
            >
              {probabilities.map((row, rowIndex) =>
                row.map((value, colIndex) => {
                  const isSelected =
                    selectedCell?.row === rowIndex && selectedCell?.col === colIndex
                  const cellKey = `${rowIndex}-${colIndex}`

                  return (
                    <div
                      key={cellKey}
                      className="relative aspect-square cursor-pointer transition-all hover:scale-110 hover:z-10"
                      style={{
                        backgroundColor: getColor(value),
                        minWidth: '30px',
                        minHeight: '30px',
                      }}
                      onClick={() => handleCellClick(rowIndex, colIndex)}
                      onMouseEnter={() => handleCellMouseEnter(rowIndex, colIndex)}
                      onMouseLeave={handleCellMouseLeave}
                      title={`Position (${colIndex}, ${rowIndex}): ${(value * 100).toFixed(1)}%`}
                    >
                      {isSelected && (
                        <div className="absolute inset-0 border-2 border-white shadow-lg"></div>
                      )}
                      {value > 0.7 && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-2 h-2 bg-white rounded-full opacity-60"></div>
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>

            {/* Axis Labels */}
            <div className="flex justify-between mt-2 px-2 text-xs text-gray-600">
              <span>X: 0m</span>
              <span>X: 10m</span>
            </div>
          </div>
        </div>

        {/* Legend and Details Panel */}
        <div className="lg:w-80 space-y-6">
          {/* Color Scale Legend */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Probability Scale</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Low (0%)</span>
                <div className="flex-1 mx-3 h-4 rounded" style={{
                  background: 'linear-gradient(to right, hsl(240, 70%, 50%), hsl(120, 70%, 50%), hsl(0, 70%, 50%))'
                }}></div>
                <span className="text-sm text-gray-600">High (100%)</span>
              </div>
              <div className="flex justify-between text-xs text-gray-500">
                <span>No Wall</span>
                <span>Uncertain</span>
                <span>Wall Detected</span>
              </div>
            </div>
          </div>

          {/* Cell Details */}
          {selectedCell && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-3">Cell Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-blue-700">Position:</span>
                  <span className="font-medium text-blue-900">
                    ({selectedCell.col}, {selectedCell.row})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Wall Probability:</span>
                  <span className="font-medium text-blue-900">
                    {(probabilities[selectedCell.row][selectedCell.col] * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-blue-700">Status:</span>
                  <span className={`font-medium ${
                    probabilities[selectedCell.row][selectedCell.col] > 0.7
                      ? 'text-red-700'
                      : probabilities[selectedCell.row][selectedCell.col] > 0.4
                      ? 'text-yellow-700'
                      : 'text-green-700'
                  }`}>
                    {probabilities[selectedCell.row][selectedCell.col] > 0.7
                      ? 'Wall Detected'
                      : probabilities[selectedCell.row][selectedCell.col] > 0.4
                      ? 'Uncertain'
                      : 'Clear'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Statistics */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Statistics</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Grid Size:</span>
                <span className="font-medium text-gray-900">
                  {rows} × {cols}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Cells with Walls:</span>
                <span className="font-medium text-gray-900">
                  {probabilities.flat().filter(v => v > 0.7).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Probability:</span>
                <span className="font-medium text-gray-900">
                  {(probabilities.flat().reduce((a, b) => a + b, 0) / (rows * cols) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Max Probability:</span>
                <span className="font-medium text-gray-900">
                  {(Math.max(...probabilities.flat()) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="font-semibold text-yellow-900 mb-2">How to Use</h3>
            <ul className="text-sm text-yellow-800 space-y-1">
              <li>• Click or hover cells for details</li>
              <li>• Red = High wall probability</li>
              <li>• Blue = Low wall probability</li>
              <li>• Grid: 10m × 10m room</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Detector Overlay Info */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-3">Detector Positions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2">
              D1
            </div>
            <p className="text-sm text-gray-700">Top-Left</p>
            <p className="text-xs text-gray-500">(0m, 0m)</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2">
              D2
            </div>
            <p className="text-sm text-gray-700">Top-Right</p>
            <p className="text-xs text-gray-500">(10m, 0m)</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2">
              D3
            </div>
            <p className="text-sm text-gray-700">Bottom-Left</p>
            <p className="text-xs text-gray-500">(0m, 10m)</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold mx-auto mb-2">
              D4
            </div>
            <p className="text-sm text-gray-700">Bottom-Right</p>
            <p className="text-xs text-gray-500">(10m, 10m)</p>
          </div>
        </div>
      </div>
    </div>
  )
}
