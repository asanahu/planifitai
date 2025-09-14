import React from 'react';
import { Info } from 'lucide-react';

interface CaloriesDisplayProps {
  calories: number;
  className?: string;
  showIcon?: boolean;
}

export function CaloriesDisplay({ calories, className = '', showIcon = true }: CaloriesDisplayProps) {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      <span>{calories}</span>
      {showIcon && (
        <div className="group relative">
          <Info className="h-3 w-3 text-gray-400 hover:text-gray-600 cursor-help" />
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap z-10">
            Estimación aproximada
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-t-2 border-transparent border-t-gray-800"></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CaloriesDisplay;
