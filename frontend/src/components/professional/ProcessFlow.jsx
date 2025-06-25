import React, { useEffect, useRef } from 'react';
import { Timeline } from 'antd';
// import { Network } from 'vis-network/standalone/esm/vis-network'; // If using vis-network for graph-like flow

const ProcessFlow = ({ steps, direction = 'vertical' }) => {
  // Placeholder for vis-network graph if needed
  // const visJsRef = useRef(null);

  // useEffect(() => {
  //   if (visJsRef.current && steps && steps.nodes && steps.edges) { // Assuming steps can also be graph data
  //     const network = new Network(visJsRef.current, steps, {});
  //     return () => {
  //       network.destroy();
  //     };
  //   }
  // }, [steps]);


  if (!steps || !Array.isArray(steps)) {
    return <p>No process steps available.</p>;
  }

  return (
    <>
      {/* For timeline view */}
      <Timeline mode={direction === 'vertical' ? 'left' : 'alternate'}>
        {steps.map((step, index) => (
          <Timeline.Item key={index} label={step.label || `Step ${index + 1}`}>
            {step.content}
          </Timeline.Item>
        ))}
      </Timeline>

      {/* For graph-like flow using vis-network (uncomment and adjust if needed) */}
      {/* <div ref={visJsRef} style={{ height: '400px', border: '1px solid #ccc' }} /> */}
    </>
  );
};

export default ProcessFlow;
