"""
Temporal analysis module for advanced analysis.

This module provides functionality for analyzing temporal patterns and trends
in data, including time series analysis, trend detection, and seasonality analysis.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class TemporalAnalyzer:
    """Analyzer for temporal patterns and trends."""
    
    def __init__(self):
        """Initialize the temporal analyzer."""
        self.time_series_available = False
        self.forecasting_available = False
        
        # Try to import time series libraries
        try:
            import statsmodels.api as sm
            from statsmodels.tsa.seasonal import seasonal_decompose
            self.time_series_available = True
            logger.info("statsmodels time series analysis available")
            
            # Try to import forecasting libraries
            try:
                from statsmodels.tsa.arima.model import ARIMA
                self.forecasting_available = True
                logger.info("ARIMA forecasting available")
            except ImportError:
                logger.warning("ARIMA forecasting not available")
                
        except ImportError:
            logger.warning("statsmodels not available for time series analysis")
    
    async def analyze(self, data: Union[List[Dict[str, Any]], pd.DataFrame], 
                     timestamp_field: str = 'timestamp',
                     value_field: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze temporal patterns in data.
        
        Args:
            data: List of dictionaries or DataFrame containing temporal data
            timestamp_field: Name of the timestamp field
            value_field: Name of the value field (optional)
            
        Returns:
            Dictionary of temporal analysis results
        """
        logger.info("Starting temporal analysis")
        
        # Convert to DataFrame if necessary
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
        
        # Ensure timestamp field exists
        if timestamp_field not in df.columns:
            return {"error": f"Timestamp field '{timestamp_field}' not found in data"}
        
        # Convert timestamps to datetime objects if they're not already
        if not pd.api.types.is_datetime64_any_dtype(df[timestamp_field]):
            df[timestamp_field] = pd.to_datetime(df[timestamp_field])
        
        # Sort by timestamp
        df = df.sort_values(timestamp_field)
        
        # Basic temporal statistics
        temporal_stats = await self._calculate_temporal_statistics(df, timestamp_field)
        
        # Time distribution analysis
        time_distribution = await self._analyze_time_distribution(df, timestamp_field)
        
        # Trend analysis
        trend_analysis = await self._analyze_trends(df, timestamp_field, value_field)
        
        # Seasonality analysis
        seasonality_analysis = await self._analyze_seasonality(df, timestamp_field, value_field)
        
        # Combine results
        results = {
            "statistics": temporal_stats,
            "time_distribution": time_distribution,
            "trends": trend_analysis,
            "seasonality": seasonality_analysis
        }
        
        return results
    
    async def _calculate_temporal_statistics(self, df: pd.DataFrame, timestamp_field: str) -> Dict[str, Any]:
        """
        Calculate basic temporal statistics.
        
        Args:
            df: DataFrame containing temporal data
            timestamp_field: Name of the timestamp field
            
        Returns:
            Dictionary of temporal statistics
        """
        try:
            # Get timestamps
            timestamps = df[timestamp_field]
            
            # Calculate time range
            start_time = timestamps.min()
            end_time = timestamps.max()
            time_range = end_time - start_time
            
            # Calculate time span in various units
            total_seconds = time_range.total_seconds()
            total_minutes = total_seconds / 60
            total_hours = total_minutes / 60
            total_days = total_hours / 24
            
            # Calculate average time between events
            if len(timestamps) > 1:
                time_diffs = timestamps.diff().dropna()
                avg_time_between = time_diffs.mean()
                median_time_between = time_diffs.median()
                min_time_between = time_diffs.min()
                max_time_between = time_diffs.max()
            else:
                avg_time_between = median_time_between = min_time_between = max_time_between = None
            
            return {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "time_range_seconds": float(total_seconds),
                "time_range_minutes": float(total_minutes),
                "time_range_hours": float(total_hours),
                "time_range_days": float(total_days),
                "event_count": len(df),
                "avg_time_between_seconds": float(avg_time_between.total_seconds()) if avg_time_between is not None else None,
                "median_time_between_seconds": float(median_time_between.total_seconds()) if median_time_between is not None else None,
                "min_time_between_seconds": float(min_time_between.total_seconds()) if min_time_between is not None else None,
                "max_time_between_seconds": float(max_time_between.total_seconds()) if max_time_between is not None else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating temporal statistics: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_time_distribution(self, df: pd.DataFrame, timestamp_field: str) -> Dict[str, Any]:
        """
        Analyze distribution of events over time.
        
        Args:
            df: DataFrame containing temporal data
            timestamp_field: Name of the timestamp field
            
        Returns:
            Dictionary of time distribution analysis results
        """
        try:
            # Get timestamps
            timestamps = df[timestamp_field]
            
            # Extract time components
            df['hour'] = timestamps.dt.hour
            df['day'] = timestamps.dt.day
            df['day_of_week'] = timestamps.dt.day_name()
            df['month'] = timestamps.dt.month
            df['year'] = timestamps.dt.year
            
            # Count events by hour of day
            events_by_hour = df.groupby('hour').size().to_dict()
            
            # Count events by day of week
            events_by_day_of_week = df.groupby('day_of_week').size().to_dict()
            
            # Count events by month
            events_by_month = df.groupby('month').size().to_dict()
            
            # Count events by year
            events_by_year = df.groupby('year').size().to_dict()
            
            # Count events by day
            df['date'] = timestamps.dt.date
            events_by_date = df.groupby('date').size()
            
            # Calculate daily statistics
            avg_events_per_day = events_by_date.mean()
            median_events_per_day = events_by_date.median()
            min_events_per_day = events_by_date.min()
            max_events_per_day = events_by_date.max()
            
            # Calculate active days percentage
            date_range = (df['date'].max() - df['date'].min()).days + 1
            active_days = len(events_by_date)
            active_days_percentage = (active_days / date_range) * 100 if date_range > 0 else 0
            
            return {
                "events_by_hour": events_by_hour,
                "events_by_day_of_week": events_by_day_of_week,
                "events_by_month": events_by_month,
                "events_by_year": events_by_year,
                "avg_events_per_day": float(avg_events_per_day),
                "median_events_per_day": float(median_events_per_day),
                "min_events_per_day": int(min_events_per_day),
                "max_events_per_day": int(max_events_per_day),
                "active_days_percentage": float(active_days_percentage)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing time distribution: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_trends(self, df: pd.DataFrame, timestamp_field: str, 
                             value_field: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze trends in temporal data.
        
        Args:
            df: DataFrame containing temporal data
            timestamp_field: Name of the timestamp field
            value_field: Name of the value field (optional)
            
        Returns:
            Dictionary of trend analysis results
        """
        try:
            # Get timestamps
            timestamps = df[timestamp_field]
            
            # If no value field is provided, analyze event frequency
            if value_field is None or value_field not in df.columns:
                # Group by day and count events
                df['date'] = timestamps.dt.date
                daily_counts = df.groupby('date').size()
                
                # Convert to time series
                ts = pd.Series(daily_counts.values, index=pd.DatetimeIndex(daily_counts.index))
                
                # Resample to ensure continuous dates
                ts = ts.resample('D').asfreq().fillna(0)
                
                # Calculate rolling averages
                rolling_7day = ts.rolling(window=7).mean()
                rolling_30day = ts.rolling(window=30).mean()
                
                # Calculate trend
                if len(ts) >= 2:
                    x = np.arange(len(ts))
                    y = ts.values
                    
                    # Simple linear regression
                    slope, intercept = np.polyfit(x, y, 1)
                    
                    trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                    trend_strength = abs(slope)
                else:
                    slope = intercept = trend_direction = trend_strength = None
                
                return {
                    "type": "event_frequency",
                    "daily_counts": daily_counts.to_dict(),
                    "rolling_7day_avg": rolling_7day.dropna().to_dict(),
                    "rolling_30day_avg": rolling_30day.dropna().to_dict(),
                    "trend_slope": float(slope) if slope is not None else None,
                    "trend_intercept": float(intercept) if intercept is not None else None,
                    "trend_direction": trend_direction,
                    "trend_strength": float(trend_strength) if trend_strength is not None else None
                }
            else:
                # Analyze trends in the value field
                values = df[value_field]
                
                # Group by day and calculate statistics
                df['date'] = timestamps.dt.date
                daily_stats = df.groupby('date')[value_field].agg(['mean', 'median', 'min', 'max', 'count'])
                
                # Convert to time series
                ts_mean = pd.Series(daily_stats['mean'].values, index=pd.DatetimeIndex(daily_stats.index))
                
                # Resample to ensure continuous dates
                ts_mean = ts_mean.resample('D').asfreq().fillna(method='ffill')
                
                # Calculate rolling averages
                rolling_7day = ts_mean.rolling(window=7).mean()
                rolling_30day = ts_mean.rolling(window=30).mean()
                
                # Calculate trend
                if len(ts_mean) >= 2:
                    x = np.arange(len(ts_mean))
                    y = ts_mean.values
                    
                    # Simple linear regression
                    slope, intercept = np.polyfit(x, y, 1)
                    
                    trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                    trend_strength = abs(slope)
                else:
                    slope = intercept = trend_direction = trend_strength = None
                
                return {
                    "type": "value_trend",
                    "field": value_field,
                    "daily_mean": daily_stats['mean'].to_dict(),
                    "daily_median": daily_stats['median'].to_dict(),
                    "daily_min": daily_stats['min'].to_dict(),
                    "daily_max": daily_stats['max'].to_dict(),
                    "daily_count": daily_stats['count'].to_dict(),
                    "rolling_7day_avg": rolling_7day.dropna().to_dict(),
                    "rolling_30day_avg": rolling_30day.dropna().to_dict(),
                    "trend_slope": float(slope) if slope is not None else None,
                    "trend_intercept": float(intercept) if intercept is not None else None,
                    "trend_direction": trend_direction,
                    "trend_strength": float(trend_strength) if trend_strength is not None else None
                }
                
        except Exception as e:
            logger.error(f"Error analyzing trends: {str(e)}")
            return {"error": str(e)}
    
    async def _analyze_seasonality(self, df: pd.DataFrame, timestamp_field: str,
                                  value_field: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze seasonality in temporal data.
        
        Args:
            df: DataFrame containing temporal data
            timestamp_field: Name of the timestamp field
            value_field: Name of the value field (optional)
            
        Returns:
            Dictionary of seasonality analysis results
        """
        if not self.time_series_available:
            return {"error": "Time series analysis not available"}
        
        try:
            # Get timestamps
            timestamps = df[timestamp_field]
            
            # If no value field is provided, analyze event frequency
            if value_field is None or value_field not in df.columns:
                # Group by day and count events
                df['date'] = timestamps.dt.date
                daily_counts = df.groupby('date').size()
                
                # Convert to time series
                ts = pd.Series(daily_counts.values, index=pd.DatetimeIndex(daily_counts.index))
                
                # Resample to ensure continuous dates
                ts = ts.resample('D').asfreq().fillna(0)
                
                # Check if we have enough data for seasonal decomposition
                if len(ts) < 14:  # Need at least 2 weeks of data
                    return {"error": "Not enough data for seasonal decomposition"}
                
                # Perform seasonal decomposition
                try:
                    from statsmodels.tsa.seasonal import seasonal_decompose
                    
                    # Determine period (7 for weekly seasonality)
                    period = 7
                    
                    # Decompose time series
                    result = seasonal_decompose(ts, model='additive', period=period)
                    
                    # Extract components
                    trend = result.trend.dropna()
                    seasonal = result.seasonal.dropna()
                    residual = result.resid.dropna()
                    
                    # Calculate seasonality strength
                    var_seasonal = np.var(seasonal)
                    var_residual = np.var(residual)
                    seasonality_strength = var_seasonal / (var_seasonal + var_residual) if (var_seasonal + var_residual) > 0 else 0
                    
                    # Get day of week pattern
                    seasonal_pattern = {}
                    for i in range(period):
                        day_values = seasonal.iloc[i::period]
                        if len(day_values) > 0:
                            seasonal_pattern[i] = float(day_values.mean())
                    
                    # Map to day names
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_pattern = {day_names[i % 7]: value for i, value in seasonal_pattern.items()}
                    
                    return {
                        "type": "event_frequency",
                        "seasonality_detected": seasonality_strength > 0.1,
                        "seasonality_strength": float(seasonality_strength),
                        "seasonal_pattern": day_pattern,
                        "trend": trend.to_dict(),
                        "seasonal": seasonal.to_dict(),
                        "residual": residual.to_dict()
                    }
                    
                except Exception as e:
                    logger.error(f"Error in seasonal decomposition: {str(e)}")
                    return {"error": f"Seasonal decomposition failed: {str(e)}"}
            else:
                # Analyze seasonality in the value field
                values = df[value_field]
                
                # Group by day and calculate mean
                df['date'] = timestamps.dt.date
                daily_means = df.groupby('date')[value_field].mean()
                
                # Convert to time series
                ts = pd.Series(daily_means.values, index=pd.DatetimeIndex(daily_means.index))
                
                # Resample to ensure continuous dates
                ts = ts.resample('D').asfreq().fillna(method='ffill')
                
                # Check if we have enough data for seasonal decomposition
                if len(ts) < 14:  # Need at least 2 weeks of data
                    return {"error": "Not enough data for seasonal decomposition"}
                
                # Perform seasonal decomposition
                try:
                    from statsmodels.tsa.seasonal import seasonal_decompose
                    
                    # Determine period (7 for weekly seasonality)
                    period = 7
                    
                    # Decompose time series
                    result = seasonal_decompose(ts, model='additive', period=period)
                    
                    # Extract components
                    trend = result.trend.dropna()
                    seasonal = result.seasonal.dropna()
                    residual = result.resid.dropna()
                    
                    # Calculate seasonality strength
                    var_seasonal = np.var(seasonal)
                    var_residual = np.var(residual)
                    seasonality_strength = var_seasonal / (var_seasonal + var_residual) if (var_seasonal + var_residual) > 0 else 0
                    
                    # Get day of week pattern
                    seasonal_pattern = {}
                    for i in range(period):
                        day_values = seasonal.iloc[i::period]
                        if len(day_values) > 0:
                            seasonal_pattern[i] = float(day_values.mean())
                    
                    # Map to day names
                    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    day_pattern = {day_names[i % 7]: value for i, value in seasonal_pattern.items()}
                    
                    return {
                        "type": "value_seasonality",
                        "field": value_field,
                        "seasonality_detected": seasonality_strength > 0.1,
                        "seasonality_strength": float(seasonality_strength),
                        "seasonal_pattern": day_pattern,
                        "trend": trend.to_dict(),
                        "seasonal": seasonal.to_dict(),
                        "residual": residual.to_dict()
                    }
                    
                except Exception as e:
                    logger.error(f"Error in seasonal decomposition: {str(e)}")
                    return {"error": f"Seasonal decomposition failed: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error analyzing seasonality: {str(e)}")
            return {"error": str(e)}
    
    async def forecast(self, data: Union[List[Dict[str, Any]], pd.DataFrame],
                      timestamp_field: str = 'timestamp',
                      value_field: Optional[str] = None,
                      forecast_periods: int = 7) -> Dict[str, Any]:
        """
        Forecast future values based on temporal data.
        
        Args:
            data: List of dictionaries or DataFrame containing temporal data
            timestamp_field: Name of the timestamp field
            value_field: Name of the value field (optional)
            forecast_periods: Number of periods to forecast
            
        Returns:
            Dictionary of forecasting results
        """
        if not self.forecasting_available:
            return {"error": "Forecasting not available"}
        
        try:
            # Convert to DataFrame if necessary
            if not isinstance(data, pd.DataFrame):
                df = pd.DataFrame(data)
            else:
                df = data.copy()
            
            # Ensure timestamp field exists
            if timestamp_field not in df.columns:
                return {"error": f"Timestamp field '{timestamp_field}' not found in data"}
            
            # Convert timestamps to datetime objects if they're not already
            if not pd.api.types.is_datetime64_any_dtype(df[timestamp_field]):
                df[timestamp_field] = pd.to_datetime(df[timestamp_field])
            
            # Sort by timestamp
            df = df.sort_values(timestamp_field)
            
            # If no value field is provided, forecast event frequency
            if value_field is None or value_field not in df.columns:
                # Group by day and count events
                df['date'] = df[timestamp_field].dt.date
                daily_counts = df.groupby('date').size()
                
                # Convert to time series
                ts = pd.Series(daily_counts.values, index=pd.DatetimeIndex(daily_counts.index))
                
                # Resample to ensure continuous dates
                ts = ts.resample('D').asfreq().fillna(0)
                
                # Check if we have enough data for forecasting
                if len(ts) < 14:  # Need at least 2 weeks of data
                    return {"error": "Not enough data for forecasting"}
                
                # Perform forecasting
                try:
                    from statsmodels.tsa.arima.model import ARIMA
                    
                    # Fit ARIMA model
                    model = ARIMA(ts, order=(1, 1, 1))
                    model_fit = model.fit()
                    
                    # Forecast future values
                    forecast = model_fit.forecast(steps=forecast_periods)
                    
                    # Create forecast dates
                    last_date = ts.index[-1]
                    forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_periods)]
                    
                    # Create forecast dictionary
                    forecast_dict = {date.strftime('%Y-%m-%d'): float(value) for date, value in zip(forecast_dates, forecast)}
                    
                    return {
                        "type": "event_frequency",
                        "forecast": forecast_dict,
                        "model_summary": str(model_fit.summary())
                    }
                    
                except Exception as e:
                    logger.error(f"Error in forecasting: {str(e)}")
                    return {"error": f"Forecasting failed: {str(e)}"}
            else:
                # Forecast values
                values = df[value_field]
                
                # Group by day and calculate mean
                df['date'] = df[timestamp_field].dt.date
                daily_means = df.groupby('date')[value_field].mean()
                
                # Convert to time series
                ts = pd.Series(daily_means.values, index=pd.DatetimeIndex(daily_means.index))
                
                # Resample to ensure continuous dates
                ts = ts.resample('D').asfreq().fillna(method='ffill')
                
                # Check if we have enough data for forecasting
                if len(ts) < 14:  # Need at least 2 weeks of data
                    return {"error": "Not enough data for forecasting"}
                
                # Perform forecasting
                try:
                    from statsmodels.tsa.arima.model import ARIMA
                    
                    # Fit ARIMA model
                    model = ARIMA(ts, order=(1, 1, 1))
                    model_fit = model.fit()
                    
                    # Forecast future values
                    forecast = model_fit.forecast(steps=forecast_periods)
                    
                    # Create forecast dates
                    last_date = ts.index[-1]
                    forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_periods)]
                    
                    # Create forecast dictionary
                    forecast_dict = {date.strftime('%Y-%m-%d'): float(value) for date, value in zip(forecast_dates, forecast)}
                    
                    return {
                        "type": "value_forecast",
                        "field": value_field,
                        "forecast": forecast_dict,
                        "model_summary": str(model_fit.summary())
                    }
                    
                except Exception as e:
                    logger.error(f"Error in forecasting: {str(e)}")
                    return {"error": f"Forecasting failed: {str(e)}"}
                
        except Exception as e:
            logger.error(f"Error in forecasting: {str(e)}")
            return {"error": str(e)}