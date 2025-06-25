import React from 'react';
import { Tree } from 'antd';

const KnowledgeTree = ({ treeData, onSelect }) => {
  return (
    <Tree
      treeData={treeData}
      onSelect={onSelect}
      // Additional props like defaultExpandAll, showLine, etc. can be added here
    />
  );
};

export default KnowledgeTree;
