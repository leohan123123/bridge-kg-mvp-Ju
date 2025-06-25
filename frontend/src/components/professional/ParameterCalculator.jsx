import React from 'react';
import { Form, InputNumber, Button, Card } from 'antd';
import { useForm, Controller } from 'react-hook-form';

const ParameterCalculator = ({ parameters, onSubmit }) => {
  const { control, handleSubmit, formState: { errors } } = useForm();

  // This is a generic calculator. Specific calculators might need more tailored UI.
  return (
    <Card title="Parameter Calculator">
      <Form onFinish={handleSubmit(onSubmit)} layout="vertical">
        {parameters && parameters.map(param => (
          <Form.Item
            key={param.name}
            label={param.label}
            validateStatus={errors[param.name] ? 'error' : ''}
            help={errors[param.name]?.message}
          >
            <Controller
              name={param.name}
              control={control}
              defaultValue={param.defaultValue || 0}
              rules={{ required: `${param.label} is required` }} // Add more specific rules as needed
              render={({ field }) => (
                <InputNumber
                  {...field}
                  style={{ width: '100%' }}
                  placeholder={`Enter ${param.label}`}
                />
              )}
            />
          </Form.Item>
        ))}
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Calculate
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ParameterCalculator;
