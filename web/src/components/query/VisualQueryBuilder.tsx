import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Button,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip,
  Grid,
} from '@mui/material';
import {
  Add,
  Delete,
  PlayArrow,
  Code,
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import type { VisualQuery, QueryTable, QueryJoin, QueryCondition, JoinType, ConditionOperator } from '@types/index';

export const VisualQueryBuilder: React.FC = () => {
  const [visualQuery, setVisualQuery] = useState<VisualQuery>({
    id: 'vq1',
    name: 'New Query',
    tables: [],
    joins: [],
    conditions: [],
    fields: [],
  });

  const [generatedSQL, setGeneratedSQL] = useState<string>('');
  const [availableTables] = useState<string[]>([
    'users',
    'orders',
    'products',
    'categories',
    'reviews',
  ]);

  const addTable = (tableName: string) => {
    const newTable: QueryTable = {
      id: `table_${Date.now()}`,
      name: tableName,
      alias: '',
      position: { x: 100, y: 100 + visualQuery.tables.length * 150 },
    };
    setVisualQuery({
      ...visualQuery,
      tables: [...visualQuery.tables, newTable],
    });
  };

  const addJoin = () => {
    if (visualQuery.tables.length < 2) return;

    const newJoin: QueryJoin = {
      id: `join_${Date.now()}`,
      leftTable: visualQuery.tables[0].id,
      rightTable: visualQuery.tables[1].id,
      leftField: 'id',
      rightField: 'id',
      type: 'INNER' as JoinType,
    };
    setVisualQuery({
      ...visualQuery,
      joins: [...visualQuery.joins, newJoin],
    });
  };

  const addCondition = () => {
    const newCondition: QueryCondition = {
      id: `cond_${Date.now()}`,
      field: '',
      operator: '=' as ConditionOperator,
      value: '',
      connector: 'AND',
    };
    setVisualQuery({
      ...visualQuery,
      conditions: [...visualQuery.conditions, newCondition],
    });
  };

  const removeTable = (id: string) => {
    setVisualQuery({
      ...visualQuery,
      tables: visualQuery.tables.filter((t) => t.id !== id),
      joins: visualQuery.joins.filter(
        (j) => j.leftTable !== id && j.rightTable !== id
      ),
    });
  };

  const removeJoin = (id: string) => {
    setVisualQuery({
      ...visualQuery,
      joins: visualQuery.joins.filter((j) => j.id !== id),
    });
  };

  const removeCondition = (id: string) => {
    setVisualQuery({
      ...visualQuery,
      conditions: visualQuery.conditions.filter((c) => c.id !== id),
    });
  };

  const generateSQL = () => {
    const { tables, joins, conditions } = visualQuery;

    if (tables.length === 0) {
      setGeneratedSQL('-- Add tables to generate SQL');
      return;
    }

    let sql = 'SELECT *\n';
    sql += `FROM ${tables[0].name}`;
    if (tables[0].alias) sql += ` AS ${tables[0].alias}`;
    sql += '\n';

    // Add joins
    joins.forEach((join) => {
      const leftTable = tables.find((t) => t.id === join.leftTable);
      const rightTable = tables.find((t) => t.id === join.rightTable);

      if (leftTable && rightTable) {
        sql += `${join.type} JOIN ${rightTable.name}`;
        if (rightTable.alias) sql += ` AS ${rightTable.alias}`;
        sql += ` ON ${leftTable.name}.${join.leftField} = ${rightTable.name}.${join.rightField}\n`;
      }
    });

    // Add conditions
    if (conditions.length > 0) {
      sql += 'WHERE ';
      conditions.forEach((cond, index) => {
        if (index > 0) sql += ` ${cond.connector} `;
        sql += `${cond.field} ${cond.operator} `;
        sql += typeof cond.value === 'string' ? `'${cond.value}'` : cond.value;
      });
      sql += '\n';
    }

    sql += 'LIMIT 100;';
    setGeneratedSQL(sql);
  };

  const onDragEnd = (result: any) => {
    // Handle drag and drop for visual query building
    if (!result.destination) return;
  };

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3 }}>
        Visual Query Builder
      </Typography>

      <Grid container spacing={2}>
        {/* Left Panel - Tables */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Available Tables
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {availableTables.map((table) => (
                <Button
                  key={table}
                  variant="outlined"
                  size="small"
                  onClick={() => addTable(table)}
                  startIcon={<Add />}
                >
                  {table}
                </Button>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Center Panel - Query Canvas */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, minHeight: 400 }}>
            <Typography variant="h6" gutterBottom>
              Query Canvas
            </Typography>

            <DragDropContext onDragEnd={onDragEnd}>
              <Droppable droppableId="tables">
                {(provided) => (
                  <Box
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    sx={{ minHeight: 300 }}
                  >
                    {visualQuery.tables.map((table, index) => (
                      <Draggable key={table.id} draggableId={table.id} index={index}>
                        {(provided) => (
                          <Paper
                            ref={provided.innerRef}
                            {...provided.draggableProps}
                            {...provided.dragHandleProps}
                            sx={{
                              p: 2,
                              mb: 2,
                              cursor: 'move',
                              bgcolor: 'background.default',
                            }}
                          >
                            <Box
                              sx={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                              }}
                            >
                              <Typography variant="subtitle1">
                                {table.name}
                                {table.alias && ` (${table.alias})`}
                              </Typography>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => removeTable(table.id)}
                              >
                                <Delete />
                              </IconButton>
                            </Box>
                          </Paper>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}
                  </Box>
                )}
              </Droppable>
            </DragDropContext>

            {/* Joins Section */}
            {visualQuery.tables.length >= 2 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Joins
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={addJoin}
                  startIcon={<Add />}
                  sx={{ mb: 1 }}
                >
                  Add Join
                </Button>

                {visualQuery.joins.map((join) => (
                  <Paper key={join.id} sx={{ p: 1, mb: 1 }}>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <FormControl size="small" sx={{ minWidth: 100 }}>
                        <Select value={join.type}>
                          <MenuItem value="INNER">INNER</MenuItem>
                          <MenuItem value="LEFT">LEFT</MenuItem>
                          <MenuItem value="RIGHT">RIGHT</MenuItem>
                          <MenuItem value="FULL">FULL</MenuItem>
                        </Select>
                      </FormControl>
                      <Typography variant="caption">JOIN</Typography>
                      <IconButton size="small" onClick={() => removeJoin(join.id)}>
                        <Delete />
                      </IconButton>
                    </Box>
                  </Paper>
                ))}
              </Box>
            )}

            {/* Conditions Section */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Conditions (WHERE)
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={addCondition}
                startIcon={<Add />}
                sx={{ mb: 1 }}
              >
                Add Condition
              </Button>

              {visualQuery.conditions.map((condition) => (
                <Paper key={condition.id} sx={{ p: 1, mb: 1 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <TextField
                      size="small"
                      placeholder="field"
                      value={condition.field}
                      sx={{ width: 120 }}
                    />
                    <FormControl size="small" sx={{ minWidth: 80 }}>
                      <Select value={condition.operator}>
                        <MenuItem value="=">=</MenuItem>
                        <MenuItem value="!=">!=</MenuItem>
                        <MenuItem value=">">{'>'}</MenuItem>
                        <MenuItem value="<">{'<'}</MenuItem>
                        <MenuItem value="LIKE">LIKE</MenuItem>
                        <MenuItem value="IN">IN</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      size="small"
                      placeholder="value"
                      value={condition.value}
                      sx={{ width: 120 }}
                    />
                    <IconButton size="small" onClick={() => removeCondition(condition.id)}>
                      <Delete />
                    </IconButton>
                  </Box>
                </Paper>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Right Panel - Generated SQL */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Generated SQL
            </Typography>

            <Button
              variant="contained"
              fullWidth
              onClick={generateSQL}
              startIcon={<Code />}
              sx={{ mb: 2 }}
            >
              Generate SQL
            </Button>

            <Paper
              sx={{
                p: 2,
                bgcolor: 'grey.900',
                color: 'common.white',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                whiteSpace: 'pre-wrap',
                minHeight: 200,
              }}
            >
              {generatedSQL || '-- Click "Generate SQL" to see the query'}
            </Paper>

            <Button
              variant="outlined"
              fullWidth
              startIcon={<PlayArrow />}
              sx={{ mt: 2 }}
              disabled={!generatedSQL}
            >
              Execute Query
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};
