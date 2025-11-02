import React from 'react';

export function GridBackground() {
  return (
    <div className="absolute inset-0 z-1 overflow-hidden">
      {/* Grid Background */}
      <div 
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(rgba(139, 0, 0, 0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139, 0, 0, 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px',
          backgroundPosition: 'center center',
        }}
      />
      
      {/* Animated Grid Lines */}
      <div className="absolute inset-0">
        {/* Horizontal Lines */}
        {[...Array(20)].map((_, i) => (
          <div
            key={`h-${i}`}
            className="absolute h-px bg-gradient-to-r from-transparent via-red-500/10 to-transparent animate-pulse"
            style={{
              top: `${(i + 1) * 5}%`,
              width: '100%',
              animationDelay: `${i * 0.2}s`,
              animationDuration: `${3 + (i % 3)}s`,
            }}
          />
        ))}
        
        {/* Vertical Lines */}
        {[...Array(20)].map((_, i) => (
          <div
            key={`v-${i}`}
            className="absolute w-px bg-gradient-to-b from-transparent via-red-500/10 to-transparent animate-pulse"
            style={{
              left: `${(i + 1) * 5}%`,
              height: '100%',
              animationDelay: `${i * 0.15}s`,
              animationDuration: `${4 + (i % 2)}s`,
            }}
          />
        ))}
      </div>

      {/* Grid Intersection Points */}
      <div className="absolute inset-0">
        {[...Array(8)].map((_, row) => (
          <div 
            key={`row-${row}`} 
            className="flex justify-center space-x-16 absolute w-full"
            style={{ top: `${row * 14 + 15}%` }}
          >
            {[...Array(6)].map((_, col) => (
              <div
                key={`point-${row}-${col}`}
                className="w-1 h-1 bg-red-400/20 rounded-full animate-ping"
                style={{
                  animationDelay: `${(row + col) * 0.3}s`,
                  animationDuration: '3s',
                }}
              />
            ))}
          </div>
        ))}
      </div>

      {/* Corner Accents */}
      <div className="absolute top-0 left-0 w-32 h-32 border-t-2 border-l-2 border-red-500/10" />
      <div className="absolute top-0 right-0 w-32 h-32 border-t-2 border-r-2 border-red-500/10" />
      <div className="absolute bottom-0 left-0 w-32 h-32 border-b-2 border-l-2 border-red-500/10" />
      <div className="absolute bottom-0 right-0 w-32 h-32 border-b-2 border-r-2 border-red-500/10" />
    </div>
  );
}
