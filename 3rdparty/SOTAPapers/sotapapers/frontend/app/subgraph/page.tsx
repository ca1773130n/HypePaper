'use client';

import { useState, useEffect, useRef } from 'react';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-data';
import { trpc } from '../../lib/trpc';

const topics = [
  { id: 'AI', label: 'Artificial Intelligence', subtopics: ['NLP', 'Computer Vision', 'Reinforcement Learning'] },
  { id: 'ML', label: 'Machine Learning', subtopics: ['Deep Learning', 'Supervised Learning', 'Unsupervised Learning'] },
  // Add more topics as needed
];

export default function SubgraphPage() {
  const [selectedTopic, setSelectedTopic] = useState('');
  const containerRef = useRef(null);
  const { data: papers } = trpc.papers.subgraph.useQuery({ task: selectedTopic });

  useEffect(() => {
    if (!papers || !containerRef.current) return;

    const nodes = new DataSet(papers.map((paper) => ({
      id: paper.id,
      label: paper.title,
    })));
    const edges = new DataSet(
      papers.flatMap((paper) =>
        paper.references.map((refId) => ({ from: paper.id, to: refId }))
      )
    );
    const data = { nodes, edges };
    const options = {
      nodes: { shape: 'dot', size: 20 },
      edges: { arrows: 'to' },
    };

    new Network(containerRef.current, data, options);
  }, [papers]);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Topic Subgraphs</h1>
      <div className="mb-4">
        {topics.map((topic) => (
          <div key={topic.id} className="mb-2">
            <button
              onClick={() => setSelectedTopic(topic.id)}
              className={`p-2 rounded ${selectedTopic === topic.id ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            >
              {topic.label}
            </button>
            {selectedTopic === topic.id && (
              <div className="ml-4 mt-2">
                {topic.subtopics.map((subtopic) => (
                  <button
                    key={subtopic}
                    onClick={() => setSelectedTopic(subtopic)}
                    className={`p-1 mr-2 rounded ${selectedTopic === subtopic ? 'bg-blue-500 text-white' : 'bg-gray-100'}`}
                  >
                    {subtopic}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
      <div ref={containerRef} className="w-full h-[600px] border" />
    </div>
  );
}
