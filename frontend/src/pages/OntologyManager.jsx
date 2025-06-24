import React, { useState, useEffect, useCallback } from 'react';
import {
    Box, Typography, Grid, Paper, TextField, Button, List, ListItem, ListItemText,
    Divider, Accordion, AccordionSummary, AccordionDetails, Chip, Alert, CircularProgress,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, IconButton,
    Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle, Snackbar
} from '@mui/material'; // Assuming Material-UI is used
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const API_BASE_URL = '/api/v1/ontology'; // Adjust if your API prefix is different

const OntologyManagerPage = () => {
    const [ontologyStructure, setOntologyStructure] = useState({ entity_types: {}, relationship_types: {} });
    const [versions, setVersions] = useState([]);
    const [updateSuggestions, setUpdateSuggestions] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

    // Form states
    const [newEntityType, setNewEntityType] = useState({ name: '', properties: '', description: '' });
    const [newRelationshipType, setNewRelationshipType] = useState({ name: '', fromTypes: '', toTypes: '', description: '' });
    const [newSnapshot, setNewSnapshot] = useState({ versionName: '', description: '' });
    const [textForSuggestions, setTextForSuggestions] = useState('');

    const showSnackbar = (message, severity = 'success') => {
        setSnackbar({ open: true, message, severity });
    };

    const fetchOntologyStructure = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/structure`);
            if (!response.ok) throw new Error(`Error fetching structure: ${response.statusText}`);
            const data = await response.json();
            setOntologyStructure(data);
        } catch (err) {
            setError(err.message);
            showSnackbar(err.message, 'error');
        } finally {
            setLoading(false);
        }
    }, []);

    const fetchVersions = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/versions`);
            if (!response.ok) throw new Error(`Error fetching versions: ${response.statusText}`);
            const data = await response.json();
            setVersions(data);
        } catch (err) {
            setError(err.message);
            showSnackbar(err.message, 'error');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchOntologyStructure();
        fetchVersions();
    }, [fetchOntologyStructure, fetchVersions]);

    const handleAddEntityType = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                entity_type: newEntityType.name,
                properties: newEntityType.properties.split(',').map(p => p.trim()).filter(p => p),
                description: newEntityType.description,
            };
            const response = await fetch(`${API_BASE_URL}/entity_type`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Error adding entity type: ${response.statusText}`);
            }
            showSnackbar(`Entity type '${newEntityType.name}' added successfully.`);
            setNewEntityType({ name: '', properties: '', description: '' });
            fetchOntologyStructure(); // Refresh structure
        } catch (err) {
            setError(err.message);
            showSnackbar(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleAddRelationshipType = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                rel_type: newRelationshipType.name,
                from_types: newRelationshipType.fromTypes.split(',').map(p => p.trim()).filter(p => p),
                to_types: newRelationshipType.toTypes.split(',').map(p => p.trim()).filter(p => p),
                description: newRelationshipType.description,
            };
            const response = await fetch(`${API_BASE_URL}/relationship_type`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Error adding relationship type: ${response.statusText}`);
            }
            showSnackbar(`Relationship type '${newRelationshipType.name}' added successfully.`);
            setNewRelationshipType({ name: '', fromTypes: '', toTypes: '', description: '' });
            fetchOntologyStructure(); // Refresh structure
        } catch (err) {
            setError(err.message);
            showSnackbar(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSnapshot = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/snapshot`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newSnapshot),
            });
            const respData = await response.json();
            if (!response.ok) {
                throw new Error(respData.detail || respData.message || `Error creating snapshot: ${response.statusText}`);
            }
            showSnackbar(`Snapshot '${newSnapshot.versionName}' created successfully.`);
            setNewSnapshot({ versionName: '', description: '' });
            fetchVersions(); // Refresh versions list
        } catch (err) {
            setError(err.message);
            showSnackbar(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleSuggestUpdates = async () => {
        if (!textForSuggestions.trim()) {
            showSnackbar('Please enter text to analyze for suggestions.', 'warning');
            return;
        }
        setLoading(true);
        setUpdateSuggestions(null); // Clear previous suggestions
        try {
            // The backend /suggest_updates endpoint expects a specific JSON structure.
            // We need to simulate an "extraction" process or simplify for this UI.
            // For now, let's assume a simplified entity extraction based on words,
            // or the user provides structured data if the backend requires it.
            // The current `OntologyAutoUpdater`'s `BridgeEntityExtractor` is a mock.
            // The API endpoint expects `{"entities": [...], "relationships": [...]}`.
            // This is a simplified client-side "extraction" for MVP.
            // A real scenario might involve sending raw text to a different endpoint for extraction first.
            const simplifiedExtractedData = {
                entities: textForSuggestions.split(/\\s+/).map(word => ({
                    text: word,
                    type_suggestion: "Unknown", // Or try to guess, e.g., capitalize for potential type
                    properties: {}
                })).slice(0,10), // Limit for test
                relationships: [] // Keep relationships empty for this simple UI test
            };

            const response = await fetch(`${API_BASE_URL}/suggest_updates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(simplifiedExtractedData),
            });
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Error getting suggestions: ${response.statusText}`);
            }
            const data = await response.json();
            setUpdateSuggestions(data);
            showSnackbar('Update suggestions received.');
        } catch (err) {
            setError(err.message);
            showSnackbar(err.message, 'error');
        } finally {
            setLoading(false);
        }
    };


    if (loading && !ontologyStructure.entity_types && !versions.length) { // Initial full page load
        return <CircularProgress />;
    }

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>本体管理 (Ontology Management)</Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            <Grid container spacing={3}>
                {/* Section 1: Ontology Structure */}
                <Grid item xs={12} md={6}>
                    <Paper elevation={3} sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>Ontology Structure</Typography>
                        {loading && Object.keys(ontologyStructure.entity_types).length === 0 && <CircularProgress size={20}/>}
                        <Accordion defaultExpanded>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Entity Types ({Object.keys(ontologyStructure.entity_types || {}).length})</Typography>
                            </AccordionSummary>
                            <AccordionDetails sx={{ maxHeight: 300, overflowY: 'auto' }}>
                                <List dense>
                                    {Object.entries(ontologyStructure.entity_types || {}).map(([type, details]) => (
                                        <ListItem key={type}>
                                            <ListItemText
                                                primary={type}
                                                secondary={`Properties: ${(details.properties || []).join(', ') || 'None'}`} />
                                        </ListItem>
                                    ))}
                                </List>
                            </AccordionDetails>
                        </Accordion>
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Relationship Types ({Object.keys(ontologyStructure.relationship_types || {}).length})</Typography>
                            </AccordionSummary>
                            <AccordionDetails sx={{ maxHeight: 300, overflowY: 'auto' }}>
                                <List dense>
                                    {Object.entries(ontologyStructure.relationship_types || {}).map(([type, details]) => (
                                        <ListItem key={type}>
                                            <ListItemText
                                                primary={type}
                                                secondary={`From: ${(details.from || ['Any']).join(', ')} To: ${(details.to || ['Any']).join(', ')}`}
                                            />
                                        </ListItem>
                                    ))}
                                </List>
                            </AccordionDetails>
                        </Accordion>
                    </Paper>
                </Grid>

                {/* Section 2: Add New Elements */}
                <Grid item xs={12} md={6}>
                    <Paper elevation={3} sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>Add to Ontology</Typography>
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography>Add Entity Type</Typography></AccordionSummary>
                            <AccordionDetails>
                                <Box component="form" onSubmit={handleAddEntityType} sx={{display: 'flex', flexDirection: 'column', gap: 2}}>
                                    <TextField label="Entity Type Name" value={newEntityType.name} onChange={e => setNewEntityType({...newEntityType, name: e.target.value})} required fullWidth />
                                    <TextField label="Properties (comma-separated)" value={newEntityType.properties} onChange={e => setNewEntityType({...newEntityType, properties: e.target.value})} required fullWidth />
                                    <TextField label="Description (optional)" value={newEntityType.description} onChange={e => setNewEntityType({...newEntityType, description: e.target.value})} fullWidth />
                                    <Button type="submit" variant="contained" startIcon={<AddIcon />} disabled={loading}>Add Entity Type</Button>
                                </Box>
                            </AccordionDetails>
                        </Accordion>
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography>Add Relationship Type</Typography></AccordionSummary>
                            <AccordionDetails>
                                <Box component="form" onSubmit={handleAddRelationshipType} sx={{display: 'flex', flexDirection: 'column', gap: 2}}>
                                    <TextField label="Relationship Type Name" value={newRelationshipType.name} onChange={e => setNewRelationshipType({...newRelationshipType, name: e.target.value})} required fullWidth />
                                    <TextField label="From Entity Types (comma-separated)" value={newRelationshipType.fromTypes} onChange={e => setNewRelationshipType({...newRelationshipType, fromTypes: e.target.value})} required fullWidth />
                                    <TextField label="To Entity Types (comma-separated)" value={newRelationshipType.toTypes} onChange={e => setNewRelationshipType({...newRelationshipType, toTypes: e.target.value})} required fullWidth />
                                    <TextField label="Description (optional)" value={newRelationshipType.description} onChange={e => setNewRelationshipType({...newRelationshipType, description: e.target.value})} fullWidth />
                                    <Button type="submit" variant="contained" startIcon={<AddIcon />} disabled={loading}>Add Relationship Type</Button>
                                </Box>
                            </AccordionDetails>
                        </Accordion>
                    </Paper>
                </Grid>

                {/* Section 3: Version Management */}
                <Grid item xs={12} md={6}>
                    <Paper elevation={3} sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>Version Management</Typography>
                        {loading && versions.length === 0 && <CircularProgress size={20}/>}
                        <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography>Create Snapshot</Typography></AccordionSummary>
                            <AccordionDetails>
                                <Box component="form" onSubmit={handleCreateSnapshot} sx={{display: 'flex', flexDirection: 'column', gap: 2}}>
                                    <TextField label="Version Name (e.g., v1.0.1)" value={newSnapshot.versionName} onChange={e => setNewSnapshot({...newSnapshot, versionName: e.target.value})} required fullWidth />
                                    <TextField label="Description (optional)" value={newSnapshot.description} onChange={e => setNewSnapshot({...newSnapshot, description: e.target.value})} fullWidth />
                                    <Button type="submit" variant="contained" startIcon={<SaveIcon />} disabled={loading}>Create Snapshot</Button>
                                </Box>
                            </AccordionDetails>
                        </Accordion>
                        <Accordion defaultExpanded>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Typography>Existing Versions ({versions.length})</Typography>
                            </AccordionSummary>
                            <AccordionDetails sx={{ maxHeight: 300, overflowY: 'auto' }}>
                                <List dense>
                                    {versions.map(v => (
                                        <ListItem key={v.name}>
                                            <ListItemText primary={v.name} secondary={`Created: ${new Date(v.timestamp).toLocaleString()} - ${v.description || 'No description'}`} />
                                        </ListItem>
                                    ))}
                                </List>
                            </AccordionDetails>
                        </Accordion>
                    </Paper>
                </Grid>

                {/* Section 4: Automatic Update Suggestions */}
                <Grid item xs={12} md={6}>
                    <Paper elevation={3} sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>Ontology Update Suggestions</Typography>
                        <TextField
                            label="Paste text for suggestions"
                            multiline
                            rows={4}
                            value={textForSuggestions}
                            onChange={e => setTextForSuggestions(e.target.value)}
                            variant="outlined"
                            fullWidth
                            sx={{ mb: 2 }}
                        />
                        <Button onClick={handleSuggestUpdates} variant="contained" startIcon={<CloudUploadIcon />} disabled={loading || !textForSuggestions.trim()}>Get Suggestions</Button>

                        {loading && updateSuggestions === null && <CircularProgress sx={{mt:1}} size={20}/>}
                        {updateSuggestions && (
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="subtitle1">Suggestions Received:</Typography>
                                {Object.entries(updateSuggestions).map(([key, valueList]) => (
                                    Array.isArray(valueList) && valueList.length > 0 && (
                                        <Box key={key} sx={{my:1}}>
                                            <Typography variant="subtitle2" component="div" sx={{textTransform: 'capitalize'}}>{key.replace(/_/g, ' ')}:</Typography>
                                            <List dense>
                                                {valueList.map((item, index) => (
                                                    <ListItem key={`${key}-${index}`}>
                                                        <ListItemText
                                                            primary={item.name || item.entity_type}
                                                            secondary={ item.properties ? `Properties: ${item.properties.join(', ')}` :
                                                                        item.from_types ? `From: ${item.from_types.join(', ')}, To: ${item.to_types.join(', ')}` :
                                                                        `Source: ${item.source_text || item.source_example || 'N/A'}`}
                                                        />
                                                    </ListItem>
                                                ))}
                                            </List>
                                        </Box>
                                    )
                                ))}
                                {Object.values(updateSuggestions).every(list => !Array.isArray(list) || list.length === 0) && <Typography>No actionable suggestions found in the response.</Typography>}
                            </Box>
                        )}
                    </Paper>
                </Grid>
            </Grid>
            <Snackbar
                open={snackbar.open}
                autoHideDuration={6000}
                onClose={() => setSnackbar({...snackbar, open: false})}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert onClose={() => setSnackbar({...snackbar, open: false})} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default OntologyManagerPage;
