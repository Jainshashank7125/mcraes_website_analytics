import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  alpha,
  useTheme,
  InputAdornment,
  CircularProgress,
} from "@mui/material";
import { Search as SearchIcon } from "@mui/icons-material";
import { motion } from "framer-motion";
import { reportingAPI } from "../../services/api";
import { debugError } from "../../utils/debug";
import Sparkline from "./Sparkline";

const GROUP_BY_OPTIONS = [
  { value: "tags", label: "By tag" },
  { value: "topics", label: "By topic" },
  { value: "prompt_variants", label: "By prompt variant" },
  { value: "stage", label: "By stage" },
  { value: "seed_prompts", label: "By seed prompt" },
];

const PromptsAnalyticsTable = ({ clientId, slug, startDate, endDate }) => {
  const theme = useTheme();
  const [groupBy, setGroupBy] = useState("seed_prompts");
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, [clientId, slug, groupBy, searchTerm, startDate, endDate, page, rowsPerPage]);

  const fetchData = async () => {
    if (!clientId && !slug) return;

    try {
      setLoading(true);
      setError(null);
      const result = await reportingAPI.getPromptsAnalytics(
        clientId,
        slug,
        groupBy,
        searchTerm || undefined,
        startDate || undefined,
        endDate || undefined,
        page,
        rowsPerPage
      );
      setData(result);
    } catch (err) {
      debugError("Error fetching prompts analytics:", err);
      setError(err.message || "Failed to fetch data");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleGroupByChange = (event) => {
    setGroupBy(event.target.value);
    setPage(0); // Reset to first page when changing group
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0); // Reset to first page when searching
  };

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatChangeIndicator = (change) => {
    if (change === null || change === undefined) return "--";
    if (change > 0) return `+${change}%`;
    if (change < 0) return `${change}%`;
    return "+00";
  };

  const getChangeColor = (change) => {
    if (change === null || change === undefined) return "text.secondary";
    if (change > 0) return "success.main";
    if (change < 0) return "error.main";
    return "text.secondary";
  };

  const getColumnHeader = () => {
    const option = GROUP_BY_OPTIONS.find((opt) => opt.value === groupBy);
    return option ? option.label.replace("By ", "") : "Item";
  };

  if (!clientId && !slug) {
    return null;
  }

  return (
    <Box sx={{ mb: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card
          sx={{
            borderRadius: 2,
            border: `1px solid ${theme.palette.divider}`,
            boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          }}
        >
          <CardContent sx={{ p: 0 }}>
            {/* Header with Search and Filter */}
            <Box
              p={3}
              borderBottom="1px solid"
              borderColor="divider"
              sx={{
                display: "flex",
                gap: 2,
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <TextField
                placeholder="Search"
                size="small"
                value={searchTerm}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  flex: 1,
                  minWidth: 200,
                  "& .MuiOutlinedInput-root": {
                    fontSize: "0.875rem",
                  },
                }}
              />
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel id="group-by-label">Group by</InputLabel>
                <Select
                  labelId="group-by-label"
                  value={groupBy}
                  label="Group by"
                  onChange={handleGroupByChange}
                >
                  {GROUP_BY_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            {/* Table */}
            {loading ? (
              <Box p={4} textAlign="center">
                <CircularProgress size={40} />
              </Box>
            ) : error ? (
              <Box p={4} textAlign="center">
                <Typography color="error">{error}</Typography>
              </Box>
            ) : !data || !data.items || data.items.length === 0 ? (
              <Box p={4} textAlign="center">
                <Typography color="text.secondary">
                  No data available
                </Typography>
              </Box>
            ) : (
              <>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow
                        sx={{
                          bgcolor: alpha(theme.palette.primary.main, 0.04),
                        }}
                      >
                        <TableCell
                          sx={{
                            fontWeight: 700,
                            fontSize: "11px",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                            py: 1.5,
                            minWidth: 200,
                          }}
                        >
                          {getColumnHeader()}
                        </TableCell>
                        <TableCell
                          sx={{
                            fontWeight: 700,
                            fontSize: "11px",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                            py: 1.5,
                            minWidth: 120,
                          }}
                        >
                          Data
                        </TableCell>
                        <TableCell
                          sx={{
                            fontWeight: 700,
                            fontSize: "11px",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                            py: 1.5,
                            minWidth: 150,
                          }}
                        >
                          Presence
                        </TableCell>
                        <TableCell
                          sx={{
                            fontWeight: 700,
                            fontSize: "11px",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                            py: 1.5,
                            minWidth: 150,
                          }}
                        >
                          Citations
                        </TableCell>
                        <TableCell
                          sx={{
                            fontWeight: 700,
                            fontSize: "11px",
                            textTransform: "uppercase",
                            letterSpacing: "0.05em",
                            py: 1.5,
                            minWidth: 200,
                          }}
                        >
                          Competitors
                        </TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {data.items.map((item, index) => (
                        <TableRow
                          key={item.key || index}
                          hover
                          sx={{
                            transition: "all 0.2s",
                            "&:hover": {
                              bgcolor: alpha(theme.palette.primary.main, 0.02),
                            },
                          }}
                        >
                          <TableCell sx={{ py: 2 }}>
                            <Box>
                              <Typography
                                variant="body2"
                                fontWeight={600}
                                sx={{
                                  fontSize: "0.875rem",
                                  mb: 0.5,
                                  lineHeight: 1.4,
                                }}
                              >
                                {item.display_name && item.display_name.length > 60
                                  ? item.display_name.substring(0, 60) + "..."
                                  : item.display_name || "N/A"}
                              </Typography>
                              {groupBy === "prompt_variants" && (
                                <Box sx={{ mt: 0.5 }}>
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ fontSize: "11px", display: "block" }}
                                  >
                                    {item.platform || "Unknown"} / {item.persona || "Unknown"}
                                  </Typography>
                                </Box>
                              )}
                              {item.stage && groupBy !== "stage" && (
                                <Chip
                                  label={item.stage}
                                  size="small"
                                  sx={{
                                    mt: 0.5,
                                    height: 20,
                                    fontSize: "10px",
                                    bgcolor: alpha(
                                      item.stage === "Awareness"
                                        ? theme.palette.info.main
                                        : item.stage === "Evaluation"
                                        ? theme.palette.warning.main
                                        : theme.palette.success.main,
                                      0.1
                                    ),
                                    color:
                                      item.stage === "Awareness"
                                        ? "info.main"
                                        : item.stage === "Evaluation"
                                        ? "warning.main"
                                        : "success.main",
                                  }}
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell sx={{ py: 2 }}>
                            <Box>
                              <Typography
                                variant="body2"
                                sx={{
                                  fontSize: "0.875rem",
                                  fontWeight: 600,
                                  mb: 0.25,
                                }}
                              >
                                {item.prompts_count?.toLocaleString() || 0}{" "}
                                prompts
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{ fontSize: "0.75rem" }}
                              >
                                {item.responses_count?.toLocaleString() || 0}{" "}
                                responses
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ py: 2 }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Sparkline
                                data={item.presence_sparkline || []}
                                color={
                                  item.presence_change > 0
                                    ? "green"
                                    : item.presence_change < 0
                                    ? "red"
                                    : "green"
                                }
                                width={100}
                                height={30}
                              />
                              <Box>
                                <Typography
                                  variant="body2"
                                  fontWeight={700}
                                  sx={{
                                    fontSize: "0.9375rem",
                                    mb: 0.25,
                                  }}
                                >
                                  {item.presence_percentage?.toFixed(1) || 0}%
                                </Typography>
                                <Typography
                                  variant="caption"
                                  color={getChangeColor(item.presence_change)}
                                  sx={{ fontSize: "0.75rem" }}
                                >
                                  {formatChangeIndicator(item.presence_change)}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ py: 2 }}>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                              }}
                            >
                              <Sparkline
                                data={item.citations_sparkline || []}
                                color={
                                  item.citations_change > 0
                                    ? "green"
                                    : item.citations_change < 0
                                    ? "red"
                                    : "green"
                                }
                                width={100}
                                height={30}
                              />
                              <Box>
                                <Typography
                                  variant="body2"
                                  fontWeight={600}
                                  sx={{
                                    fontSize: "0.9375rem",
                                    mb: 0.25,
                                  }}
                                >
                                  {item.citations_count?.toLocaleString() || 0}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  color={getChangeColor(item.citations_change)}
                                  sx={{ fontSize: "0.75rem" }}
                                >
                                  {formatChangeIndicator(item.citations_change)}
                                </Typography>
                              </Box>
                            </Box>
                          </TableCell>
                          <TableCell sx={{ py: 2 }}>
                            {item.competitors && item.competitors.length > 0 ? (
                              <Box>
                                {item.competitors.slice(0, 3).map((comp, idx) => (
                                  <Typography
                                    key={idx}
                                    variant="caption"
                                    sx={{
                                      fontSize: "0.75rem",
                                      display: "block",
                                      mb: 0.25,
                                    }}
                                  >
                                    {comp.name} ({comp.percentage}%)
                                  </Typography>
                                ))}
                                {item.competitors.length > 3 && (
                                  <Typography
                                    variant="caption"
                                    color="text.secondary"
                                    sx={{ fontSize: "0.75rem" }}
                                  >
                                    +{item.competitors.length - 3} more
                                  </Typography>
                                )}
                              </Box>
                            ) : (
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{ fontSize: "0.75rem" }}
                              >
                                --
                              </Typography>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {/* Pagination */}
                {data.total_count > 0 && (
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      px: 2,
                      py: 1.5,
                      borderTop: `1px solid ${theme.palette.divider}`,
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {data.total_count} rows
                    </Typography>
                    <TablePagination
                      component="div"
                      count={data.total_count}
                      page={page}
                      onPageChange={handlePageChange}
                      rowsPerPage={rowsPerPage}
                      onRowsPerPageChange={handleRowsPerPageChange}
                      rowsPerPageOptions={[5, 10, 25, 50]}
                      sx={{
                        "& .MuiTablePagination-toolbar": {
                          px: 0,
                        },
                        "& .MuiTablePagination-selectLabel": {
                          fontSize: "0.875rem",
                          color: "text.secondary",
                        },
                        "& .MuiTablePagination-displayedRows": {
                          fontSize: "0.875rem",
                        },
                      }}
                    />
                  </Box>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </Box>
  );
};

export default PromptsAnalyticsTable;

