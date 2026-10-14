"""Job provider interface specification."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class JobProvider(ABC):
    """Abstract base class interface for job market telemetry data providers."""

    @abstractmethod
    def search_jobs(
        self,
        query: str = "",
        location: str = "",
        page: int = 1,
        results_per_page: int = 20,
        country: Optional[str] = None,
        category: Optional[str] = None,
        what_or: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search job postings.
        
        Returns dictionary containing:
        - results: List of standardized job dicts
        - total_count: Total available listings
        - is_sample_data: True if served from sample fixtures, False if live API
        - data_source: Provider name string
        """
        pass

