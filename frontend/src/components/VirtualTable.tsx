import React from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';

// Define a more specific type for your data items if possible
// For example, if each item is an object with id and text:
// interface DataItem {
//   id: number;
//   text: string;
// }
// type DataType = DataItem[];

// Using a generic type for now
type DataType = any[];

interface VirtualTableProps {
  data: DataType;
  itemSize?: number; // Optional: height of each row
  renderRow: (item: any, style: React.CSSProperties, index: number) => React.ReactNode; // Function to render each row
}

const VirtualTable: React.FC<VirtualTableProps> = ({ data, itemSize = 50, renderRow }) => {
  const Row = ({ index, style }: ListChildComponentProps) => {
    return renderRow(data[index], style, index);
  };

  if (!data || data.length === 0) {
    return <div>No data to display.</div>;
  }

  return (
    <AutoSizer>
      {({ height, width }) => (
        <List
          height={height}
          itemCount={data.length}
          itemSize={itemSize}
          width={width}
        >
          {Row}
        </List>
      )}
    </AutoSizer>
  );
};

export default VirtualTable;

// Example Usage (can be in another component):
/*
import VirtualTable from './VirtualTable';

const MyComponentWithVirtualTable = () => {
  // Sample data: array of objects
  const sampleData = Array.from({ length: 1000 }, (_, index) => ({
    id: index,
    name: `Item ${index + 1}`,
    value: Math.random() * 100,
  }));

  // Custom row renderer
  const renderDataRow = (item: any, style: React.CSSProperties, index: number) => (
    <div style={style} className={`row ${index % 2 === 0 ? 'even-row' : 'odd-row'}`}>
      <span>ID: {item.id}</span>
      <span>Name: {item.name}</span>
      <span>Value: {item.value.toFixed(2)}</span>
    </div>
  );

  return (
    <div style={{ height: '500px', width: '100%' }}>
      <h2>Virtualized List Example</h2>
      <VirtualTable data={sampleData} itemSize={35} renderRow={renderDataRow} />
    </div>
  );
};

// CSS for example usage:
// .row {
//   display: flex;
//   justify-content: space-between;
//   padding: 0 10px;
//   align-items: center;
//   border-bottom: 1px solid #eee;
// }
// .even-row {
//   background-color: #f9f9f9;
// }
// .odd-row {
//   background-color: #fff;
// }

export default MyComponentWithVirtualTable;
*/
