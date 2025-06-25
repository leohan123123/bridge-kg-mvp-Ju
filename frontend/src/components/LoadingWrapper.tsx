import React from 'react';
import { Spin } from 'antd';

interface LoadingWrapperProps {
  loading: boolean;
  children: React.ReactNode;
}

const LoadingWrapper: React.FC<LoadingWrapperProps> = ({ loading, children }) => (
  loading ? <Spin size="large" /> : <>{children}</>
);

export default LoadingWrapper;
