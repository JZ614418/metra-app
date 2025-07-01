import React from 'react';
import ModelRecommend from '@/components/ModelRecommend';

const ModelSelection = () => {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-2">Model Selection</h1>
      <p className="text-gray-500 mb-6">Get smart recommendations for the best open-source model for your task.</p>
      <ModelRecommend />
    </div>
  );
};

export default ModelSelection; 