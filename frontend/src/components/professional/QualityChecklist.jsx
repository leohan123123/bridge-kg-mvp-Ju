import React, { useState } from 'react';
import { Checkbox, List, Button, Typography, Card } from 'antd';

const { Title } = Typography;

const QualityChecklist = ({ items, title = "Quality Checklist", onGenerate }) => {
  const [checkedItems, setCheckedItems] = useState({});

  const handleCheck = (itemId, isChecked) => {
    setCheckedItems(prev => ({ ...prev, [itemId]: isChecked }));
  };

  // This is a basic checklist. A generator might involve more complex logic
  // for selecting items based on criteria.
  return (
    <Card>
      <Title level={4}>{title}</Title>
      {onGenerate && (
        <Button onClick={onGenerate} type="primary" style={{ marginBottom: 16 }}>
          Generate Checklist
        </Button>
      )}
      {items && items.length > 0 ? (
        <List
          bordered
          dataSource={items}
          renderItem={item => (
            <List.Item>
              <Checkbox
                checked={!!checkedItems[item.id]}
                onChange={e => handleCheck(item.id, e.target.checked)}
              >
                {item.label}
              </Checkbox>
            </List.Item>
          )}
        />
      ) : (
        <p>No checklist items available. {onGenerate ? "Try generating a new checklist." : ""}</p>
      )}
    </Card>
  );
};

export default QualityChecklist;
