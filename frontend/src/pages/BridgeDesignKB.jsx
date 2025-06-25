import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios'; // Assuming axios is used for API calls

// Mock API base URL, replace with your actual API endpoint
const API_BASE_URL = '/api/v1/bridge_design'; // Adjust if your FastAPI prefix is different

// Basic styling (replace with your actual CSS or UI library)
const styles = {
  container: { padding: '20px', fontFamily: 'Arial, sans-serif' },
  section: { marginBottom: '30px', padding: '15px', border: '1px solid #eee', borderRadius: '5px' },
  title: { marginTop: '0', borderBottom: '2px solid #333', paddingBottom: '5px' },
  subTitle: { marginTop: '10px', color: '#555' },
  input: { marginRight: '10px', padding: '8px', minWidth: '200px' },
  button: { padding: '8px 15px', cursor: 'pointer' },
  pre: { backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px', whiteSpace: 'pre-wrap', wordBreak: 'break-all' },
  error: { color: 'red', border: '1px solid red', padding: '10px', margin: '10px 0' },
  tabs: { display: 'flex', marginBottom: '10px', borderBottom: '1px solid #ccc' },
  tab: { padding: '10px 15px', cursor: 'pointer', border: '1px solid transparent', borderBottom: 'none' },
  activeTab: { border: '1px solid #ccc', borderBottom: '1px solid white', fontWeight: 'bold',  position: 'relative', top: '1px' },
  visualizationPlaceholder: {
    width: '100%', height: '300px', border: '1px dashed #ccc',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: '#aaa', fontStyle: 'italic', textAlign: 'center'
  },
  listItem: { padding: '5px 0', borderBottom: '1px dotted #eee' }
};

function BridgeDesignKB() {
  const [activeTab, setActiveTab] = useState('ontology');

  // Ontology state
  const [ontology, setOntology] = useState(null);
  const [ontologyError, setOntologyError] = useState('');

  // Knowledge Extraction state
  const [extractionText, setExtractionText] = useState('主梁设计应考虑弯矩和剪力。根据GB50010规范，混凝土强度等级不低于C30。跨径为50m。');
  const [extractionResult, setExtractionResult] = useState(null);
  const [extractionError, setExtractionError] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);

  // Design Standards state
  const [standards, setStandards] = useState(null); // Can be list of codes, hierarchy, or single standard
  const [standardCodeQuery, setStandardCodeQuery] = useState('');
  const [standardsError, setStandardsError] = useState('');
  const [fetchHierarchy, setFetchHierarchy] = useState(false);

  // Design Calculation state
  const [calcMethods, setCalcMethods] = useState([]);
  const [selectedCalcMethod, setSelectedCalcMethod] = useState('');
  const [calcParams, setCalcParams] = useState(''); // JSON string for params
  const [calcResult, setCalcResult] = useState(null);
  const [calcError, setCalcError] = useState('');

  // Generic loading/error for API calls
  const [loading, setLoading] = useState(false);

  // Fetch Ontology
  const fetchOntology = useCallback(async () => {
    setLoading(true);
    setOntologyError('');
    try {
      const response = await axios.get(`${API_BASE_URL}/ontology`);
      setOntology(response.data);
    } catch (error) {
      setOntologyError(error.response?.data?.detail || error.message || 'Failed to fetch ontology.');
      setOntology(null);
    }
    setLoading(false);
  }, []);

  // Fetch Design Standards
  const fetchDesignStandards = useCallback(async () => {
    setLoading(true);
    setStandardsError('');
    let url = `${API_BASE_URL}/standards`;
    const params = {};
    if (standardCodeQuery && !fetchHierarchy) {
      params.standard_code = standardCodeQuery;
    }
    if (fetchHierarchy) {
      params.hierarchy = true;
    }

    try {
      const response = await axios.get(url, { params });
      setStandards(response.data);
    } catch (error) {
      setStandardsError(error.response?.data?.detail || error.message || 'Failed to fetch standards.');
      setStandards(null);
    }
    setLoading(false);
  }, [standardCodeQuery, fetchHierarchy]);

  // Fetch Calculation Methods
  const fetchCalcMethods = useCallback(async () => {
    setLoading(true);
    setCalcError(''); // Clear previous errors
    try {
      const response = await axios.get(`${API_BASE_URL}/calculation_methods`);
      setCalcMethods(response.data || []);
      if (response.data && response.data.length > 0) {
        setSelectedCalcMethod(response.data[0].name); // Default to first method
      }
    } catch (error) {
      setCalcError(error.response?.data?.detail || error.message || 'Failed to fetch calculation methods.');
      setCalcMethods([]);
    }
    setLoading(false);
  }, []);


  // Initial data fetches
  useEffect(() => {
    if (activeTab === 'ontology') fetchOntology();
    if (activeTab === 'standards') fetchDesignStandards();
    if (activeTab === 'calculations') fetchCalcMethods();
  }, [activeTab, fetchOntology, fetchDesignStandards, fetchCalcMethods]);

  const handleExtractionSubmit = async (e) => {
    e.preventDefault();
    setIsExtracting(true);
    setExtractionError('');
    setExtractionResult(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/extract_knowledge`, { text: extractionText });
      setExtractionResult(response.data);
    } catch (error) {
      setExtractionError(error.response?.data?.detail || error.message || 'Failed to extract knowledge.');
    }
    setIsExtracting(false);
  };

  const handleCalculationSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setCalcError('');
    setCalcResult(null);
    let paramsObject;
    try {
      paramsObject = calcParams ? JSON.parse(calcParams) : {};
    } catch (jsonError) {
      setCalcError('Invalid JSON format for parameters.');
      setLoading(false);
      return;
    }
    try {
      const response = await axios.post(`${API_BASE_URL}/execute_calculation`, {
        method_name: selectedCalcMethod,
        parameters: paramsObject,
      });
      setCalcResult(response.data);
    } catch (error) {
      setCalcError(error.response?.data?.detail || error.message || 'Calculation failed.');
    }
    setLoading(false);
  };

  const renderOntology = () => (
    <div style={styles.section}>
      <h2 style={styles.title}>设计理论知识浏览 (本体)</h2>
      {loading && <p>Loading ontology...</p>}
      {ontologyError && <div style={styles.error}>{ontologyError}</div>}
      {ontology && <pre style={styles.pre}>{JSON.stringify(ontology, null, 2)}</pre>}
    </div>
  );

  const renderKnowledgeExtraction = () => (
    <div style={styles.section}>
      <h2 style={styles.title}>设计知识抽取</h2>
      <form onSubmit={handleExtractionSubmit}>
        <textarea
          value={extractionText}
          onChange={(e) => setExtractionText(e.target.value)}
          rows={5}
          style={{ width: '100%', padding: '8px', boxSizing: 'border-box', marginBottom: '10px' }}
          placeholder="输入包含设计知识的文本..."
        />
        <button type="submit" style={styles.button} disabled={isExtracting}>
          {isExtracting ? '正在提取...' : '提取知识'}
        </button>
      </form>
      {extractionError && <div style={styles.error}>{extractionError}</div>}
      {extractionResult && (
        <div>
          <h3 style={styles.subTitle}>提取结果:</h3>
          <pre style={styles.pre}>{JSON.stringify(extractionResult, null, 2)}</pre>
        </div>
      )}
    </div>
  );

  const renderDesignStandards = () => (
    <div style={styles.section}>
      <h2 style={styles.title}>设计规范条文检索</h2>
      <form onSubmit={(e) => { e.preventDefault(); fetchDesignStandards(); }}>
        <input
          type="text"
          style={styles.input}
          value={standardCodeQuery}
          onChange={(e) => setStandardCodeQuery(e.target.value)}
          placeholder="输入规范编号 (如 GB50011)"
        />
        <label style={{marginRight: '10px'}}>
          <input
            type="checkbox"
            checked={fetchHierarchy}
            onChange={(e) => setFetchHierarchy(e.target.checked)}
          />
          获取层级结构
        </label>
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? '查询中...' : '查询规范'}
        </button>
      </form>
      {standardsError && <div style={styles.error}>{standardsError}</div>}
      {standards && (
        <div>
          <h3 style={styles.subTitle}>规范信息:</h3>
          <pre style={styles.pre}>{JSON.stringify(standards, null, 2)}</pre>
        </div>
      )}
    </div>
  );

  const renderCalculations = () => (
    <div style={styles.section}>
      <h2 style={styles.title}>计算方法和公式查询/执行</h2>
      {loading && !calcMethods.length && <p>Loading calculation methods...</p>}

      <h3 style={styles.subTitle}>可用计算方法:</h3>
      {calcMethods.length > 0 ? (
        <select
          value={selectedCalcMethod}
          onChange={(e) => setSelectedCalcMethod(e.target.value)}
          style={{...styles.input, marginBottom: '10px'}}
        >
          {calcMethods.map(method => (
            <option key={method.name} value={method.name}>
              {method.name} - {method.description}
            </option>
          ))}
        </select>
      ) : (
        <p>No calculation methods loaded or available.</p>
      )}

      {selectedCalcMethod && calcMethods.find(m => m.name === selectedCalcMethod) && (
        <div style={{fontSize: '0.9em', color: '#666', marginBottom: '10px'}}>
          <p><strong>参数:</strong> {calcMethods.find(m => m.name === selectedCalcMethod).parameters?.join(', ') || 'N/A'}</p>
          <p><strong>输出:</strong> {calcMethods.find(m => m.name === selectedCalcMethod).outputs?.join(', ') || 'N/A'}</p>
        </div>
      )}

      <form onSubmit={handleCalculationSubmit}>
        <textarea
          value={calcParams}
          onChange={(e) => setCalcParams(e.target.value)}
          rows={3}
          style={{ width: '100%', padding: '8px', boxSizing: 'border-box', marginBottom: '10px' }}
          placeholder='输入参数 (JSON格式), e.g., {"point_load_P": 100, "span_L": 5}'
        />
        <button type="submit" style={styles.button} disabled={loading || !selectedCalcMethod}>
          {loading ? '计算中...' : '执行计算'}
        </button>
      </form>
      {calcError && <div style={styles.error}>{calcError}</div>}
      {calcResult && (
        <div>
          <h3 style={styles.subTitle}>计算结果:</h3>
          <pre style={styles.pre}>{JSON.stringify(calcResult, null, 2)}</pre>
        </div>
      )}
    </div>
  );

  const renderParametersAndConstraints = () => (
    <div style={styles.section}>
      <h2 style={styles.title}>设计参数和约束展示</h2>
      <p>此部分通常会从“知识抽取”或特定查询中获取参数和约束信息。</p>
      <p>例如，在知识抽取结果中：</p>
      {extractionResult?.parameters && (
        <>
          <h3 style={styles.subTitle}>提取到的参数:</h3>
          <ul>
            {extractionResult.parameters.map((p, i) => (
              <li key={`param-${i}`} style={styles.listItem}>{p.keyword || p.parameter_name}: {p.value || 'N/A'} {p.unit || ''}</li>
            ))}
          </ul>
        </>
      )}
      {extractionResult?.constraints && (
         <>
          <h3 style={styles.subTitle}>提取到的约束:</h3>
          <ul>
            {extractionResult.constraints.map((c, i) => (
              <li key={`constraint-${i}`} style={styles.listItem}>{c.keyword}: {c.description}</li>
            ))}
          </ul>
        </>
      )}
      {!extractionResult?.parameters && !extractionResult?.constraints && (
        <p><i>请先在“设计知识抽取”标签页中提取知识以查看参数和约束。</i></p>
      )}
    </div>
  );

  const renderKnowledgeGraphVis = () => (
    <div style={styles.section}>
      <h2 style={styles.title}>设计知识关联图谱可视化</h2>
      <div style={styles.visualizationPlaceholder}>
        <p>知识图谱可视化区域</p>
        <p>(例如使用 Vis.js, Cytoscape.js, or D3.js)</p>
        <p>此功能需要专门的图数据和渲染逻辑。</p>
      </div>
      <p>
        图谱数据可以从本体、提取的知识及其依赖关系、或规范层级构建。
        例如，本体的结构、或 `link_design_dependencies` 的输出可以作为图谱数据源。
      </p>
      {extractionResult?.dependencies && (
         <>
          <h3 style={styles.subTitle}>提取到的依赖关系 (可用于图谱):</h3>
          <pre style={styles.pre}>{JSON.stringify(extractionResult.dependencies, null, 2)}</pre>
        </>
      )}
    </div>
  );


  const renderTabContent = () => {
    switch (activeTab) {
      case 'ontology':
        return renderOntology();
      case 'extraction':
        return renderKnowledgeExtraction();
      case 'standards':
        return renderDesignStandards();
      case 'calculations':
        return renderCalculations();
      case 'params_constraints':
        return renderParametersAndConstraints();
      case 'graph_vis':
        return renderKnowledgeGraphVis();
      default:
        return <p>Select a tab.</p>;
    }
  };

  const tabs = [
    { id: 'ontology', label: '设计理论 (本体)' },
    { id: 'extraction', label: '知识抽取' },
    { id: 'standards', label: '设计规范' },
    { id: 'calculations', label: '计算方法' },
    { id: 'params_constraints', label: '参数与约束' },
    { id: 'graph_vis', label: '知识图谱可视化' },
  ];

  return (
    <div style={styles.container}>
      <h1>桥梁设计专业知识库</h1>

      <div style={styles.tabs}>
        {tabs.map(tab => (
          <div
            key={tab.id}
            style={{...styles.tab, ...(activeTab === tab.id ? styles.activeTab : {})}}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </div>
        ))}
      </div>

      {renderTabContent()}
    </div>
  );
}

export default BridgeDesignKB;
