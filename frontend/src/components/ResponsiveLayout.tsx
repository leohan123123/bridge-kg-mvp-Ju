import React from 'react';
import { Grid } from 'antd';
import './ResponsiveLayout.css'; // We'll create this CSS file next

const { useBreakpoint } = Grid;

interface ResponsiveLayoutProps {
  children: React.ReactNode;
}

const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ children }) => {
  const screens = useBreakpoint();

  // Determine layout class based on breakpoints
  // Example: 'xs' for extra small, 'md' for medium, etc.
  // You can customize these classes and logic as needed.
  let layoutClass = 'mobile-layout'; // Default to mobile
  if (screens.xxl) {
    layoutClass = 'desktop-layout xxl';
  } else if (screens.xl) {
    layoutClass = 'desktop-layout xl';
  } else if (screens.lg) {
    layoutClass = 'desktop-layout lg';
  } else if (screens.md) {
    layoutClass = 'desktop-layout md';
  } else if (screens.sm) {
    layoutClass = 'mobile-layout sm';
  } else if (screens.xs) {
    layoutClass = 'mobile-layout xs';
  }

  return (
    <div className={layoutClass}>
      {/* Example of conditionally rendering elements based on screen size */}
      {screens.md ? (
        <p>This is a desktop or larger screen ({Object.keys(screens).filter(key => screens[key]).join(', ')}).</p>
      ) : (
        <p>This is a mobile screen ({Object.keys(screens).filter(key => screens[key]).join(', ')}).</p>
      )}
      {children}
    </div>
  );
};

export default ResponsiveLayout;
