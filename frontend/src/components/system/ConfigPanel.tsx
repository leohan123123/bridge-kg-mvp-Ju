import React from 'react';
import { Form, Input, Button, Typography, Card, Space } from 'antd';
import type { FormInstance } from 'antd';

const { Title, Paragraph } = Typography;

// This is a basic placeholder for a ConfigPanel.
// A true dynamic form generator would require a schema to define fields, types, validation, etc.
// Ant Design's Form component is used here directly.

interface ConfigField {
    name: string;
    label: string;
    type: 'string' | 'number' | 'boolean' | 'select'; // Extend as needed
    required?: boolean;
    options?: { label: string; value: string | number }[]; // For select type
    defaultValue?: any;
}

interface ConfigPanelProps {
    title?: string;
    configSchema?: ConfigField[]; // Simplified schema for now
    initialValues?: Record<string, any>;
    onSave?: (values: Record<string, any>) => void;
    form?: FormInstance; // Allow passing an external form instance
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({
    title = "Configuration Panel",
    configSchema,
    initialValues,
    onSave,
    form: externalForm,
}) => {
    const [internalForm] = Form.useForm();
    const form = externalForm || internalForm;

    const handleSave = (values: Record<string, any>) => {
        if (onSave) {
            onSave(values);
        }
        console.log("ConfigPanel Save:", values);
    };

    // Basic dynamic field rendering (very simplified)
    const renderFormItems = () => {
        if (!configSchema) {
            return <Paragraph type="secondary">No configuration schema provided. Using placeholder fields.</Paragraph>;
        }
        return configSchema.map(field => (
            <Form.Item
                key={field.name}
                name={field.name}
                label={field.label}
                rules={[{ required: field.required, message: `${field.label} is required` }]}
                initialValue={field.defaultValue}
            >
                {/* Basic input type mapping */}
                {field.type === 'number' ? <Input type="number" /> : <Input />}
                {/* TODO: Add Select, Checkbox for boolean, etc. */}
            </Form.Item>
        ));
    };

    return (
        <Card title={title}>
            <Paragraph type="secondary">
                This is a placeholder for a ConfigPanel. Features like dynamic form generation
                from a schema, parameter validation, and preset management would be built here.
            </Paragraph>
            <Form
                form={form}
                layout="vertical"
                initialValues={initialValues}
                onFinish={handleSave}
            >
                {configSchema ? renderFormItems() : (
                    <>
                        <Form.Item name="param1" label="Placeholder Param 1">
                            <Input />
                        </Form.Item>
                        <Form.Item name="param2" label="Placeholder Param 2">
                            <Input />
                        </Form.Item>
                    </>
                )}
                <Form.Item>
                    <Space>
                        <Button type="primary" htmlType="submit">
                            Save Configuration
                        </Button>
                        <Button onClick={() => form.resetFields()}>
                            Reset
                        </Button>
                        {/* TODO: Add preset management buttons */}
                    </Space>
                </Form.Item>
            </Form>
        </Card>
    );
};

export default ConfigPanel;
