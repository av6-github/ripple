"""
Parser for ARFF Polish Bankruptcy Datasets
"""

import os
from typing import Dict, Any, List, Optional
import numpy as np
from scipy.io import arff

from backend.domain.schemas import FinancialStatementData
from backend.domain.enums import SourceType, Confidence, ForecastingCase


class ARFFParser:
    """Extracts instances from Polish Companies Bankruptcy ARFF files."""
    
    @staticmethod
    def parse_file(file_path: str, source_ref: Optional[str] = None) -> List[FinancialStatementData]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ARFF file not found: {file_path}")
            
        source_name = source_ref or os.path.basename(file_path)
        
        # Determine forecasting case from filename
        case = ForecastingCase.AD_HOC
        for c in ForecastingCase:
            if c.value in source_name.lower():
                case = c
                break

        data, meta = arff.loadarff(file_path)
        records: List[FinancialStatementData] = []
        
        for row in data:
            raw_ratios: Dict[str, Optional[float]] = {}
            for i in range(1, 65):
                attr_name = f"Attr{i}"
                val = row[attr_name]
                if np.isnan(val):
                    raw_ratios[attr_name] = None
                else:
                    raw_ratios[attr_name] = float(val)
                    
            # Extract raw monetary working capital (Attr55)
            wc_val = raw_ratios.get("Attr55")
            
            stmt = FinancialStatementData(
                working_capital=wc_val,
                raw_ratios=raw_ratios,
                source_type=SourceType.PUBLIC_DATASET,
                source_ref=source_name,
                confidence=Confidence.VERIFIED
            )
            records.append(stmt)
            
        return records
