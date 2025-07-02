import React from 'react';

const SchemaDisplay = ({ schema }: { schema: any }) => {
  if (!schema || typeof schema !== 'object') {
    return <pre className="text-xs">{JSON.stringify(schema, null, 2)}</pre>;
  }

  const renderValue = (value: any): React.ReactNode => {
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object' && value !== null) {
      return (
        <ul className="list-disc list-inside pl-4">
          {Object.entries(value).map(([key, val]) => (
            <li key={key}>
              <span className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</span> {renderValue(val)}
            </li>
          ))}
        </ul>
      );
    }
    return value;
  };

  return (
    <div className="space-y-2 text-sm">
      {Object.entries(schema).map(([key, value]) => (
        <div key={key}>
          <p className="font-semibold capitalize">{key.replace(/_/g, ' ')}:</p>
          <div className="pl-4 text-muted-foreground">{renderValue(value)}</div>
        </div>
      ))}
    </div>
  );
};

export default SchemaDisplay; 