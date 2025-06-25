import React from 'react';
import { Input } from 'antd';

const { Search } = Input;

const ProfessionalSearch = ({ onSearch }) => {
  return (
    <Search
      placeholder="Enter search keyword"
      onSearch={onSearch}
      enterButton
      style={{ width: 300 }}
    />
  );
};

export default ProfessionalSearch;
