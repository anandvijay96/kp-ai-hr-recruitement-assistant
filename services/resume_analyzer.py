import re
import logging
from typing import Dict, List, Any
from collections import Counter

logger = logging.getLogger(__name__)

class ResumeAuthenticityAnalyzer:
    """Analyzes resume authenticity using multiple criteria"""

    def __init__(self):
        try:
            import nltk
            # Download required NLTK data if not available
            for resource in ['punkt', 'punkt_tab']:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except (LookupError, OSError):
                    try:
                        nltk.download(resource, quiet=True)
                    except Exception as e:
                        logger.warning(f"Could not download NLTK {resource}: {e}")
        except ImportError:
            logger.warning("NLTK not available for grammar analysis")

    def analyze_authenticity(self, text_content: str, structure_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze resume authenticity using multiple criteria"""

        scores = {
            'font_consistency': self._analyze_font_consistency(structure_info),
            'grammar_quality': self._analyze_grammar_quality(text_content),
            'formatting_consistency': self._analyze_formatting_consistency(structure_info),
            'content_suspicious_patterns': self._analyze_suspicious_patterns(text_content),
            'structure_consistency': self._analyze_structure_consistency(structure_info)
        }

        # Calculate overall score (weighted average)
        weights = {
            'font_consistency': 0.25,
            'grammar_quality': 0.25,
            'formatting_consistency': 0.20,
            'content_suspicious_patterns': 0.15,
            'structure_consistency': 0.15
        }

        overall_score = sum(scores[criteria] * weights[criteria] for criteria in scores)

        return {
            'overall_score': round(overall_score, 1),
            'font_consistency': round(scores['font_consistency'], 1),
            'grammar_score': round(scores['grammar_quality'], 1),
            'formatting_score': round(scores['formatting_consistency'], 1),
            'visual_consistency': round(scores['structure_consistency'], 1),
            'details': self._generate_analysis_details(scores, text_content)
        }

    def _analyze_font_consistency(self, structure_info: Dict[str, Any]) -> float:
        """Analyze font consistency across the document"""
        try:
            font_analysis = structure_info.get('font_analysis', {})
            unique_fonts = font_analysis.get('unique_fonts', 0)

            # Fewer fonts = more consistent = higher score
            if unique_fonts <= 2:
                return 95.0
            elif unique_fonts <= 4:
                return 85.0
            elif unique_fonts <= 6:
                return 70.0
            else:
                return 50.0
        except Exception as e:
            logger.error(f"Font consistency analysis failed: {str(e)}")
            return 75.0  # Default moderate score

    def _analyze_grammar_quality(self, text_content: str) -> float:
        """Analyze grammar quality and language patterns"""
        try:
            import nltk
            from nltk.tokenize import sent_tokenize, word_tokenize

            sentences = sent_tokenize(text_content)
            words = word_tokenize(text_content)

            if not sentences or not words:
                return 50.0

            # Check for common grammar issues
            grammar_issues = 0

            # Check sentence length consistency
            sentence_lengths = [len(word_tokenize(sent)) for sent in sentences]
            avg_length = sum(sentence_lengths) / len(sentence_lengths)

            # Flag very short or very long sentences
            for length in sentence_lengths:
                if length < 3 or length > 50:
                    grammar_issues += 1

            # Check for excessive capitalization (SCREAMING TEXT)
            capitalized_words = sum(1 for word in words if word.isupper() and len(word) > 3)
            if capitalized_words > len(words) * 0.1:  # More than 10% capitalized
                grammar_issues += 2

            # Check for excessive punctuation
            punctuation_count = sum(1 for char in text_content if char in '!@#$%^&*()')
            if punctuation_count > len(text_content) * 0.05:  # More than 5% punctuation
                grammar_issues += 1

            # Calculate score (inverse of issues)
            max_issues = len(sentences) * 0.3  # Allow 30% of sentences to have issues
            issue_penalty = min(grammar_issues / max(max_issues, 1), 1.0)

            return max(0, 100 - (issue_penalty * 50))

        except ImportError:
            # Fallback if NLTK not available
            return self._basic_grammar_check(text_content)
        except Exception as e:
            logger.error(f"Grammar analysis failed: {str(e)}")
            return 75.0

    def _basic_grammar_check(self, text_content: str) -> float:
        """Basic grammar check without NLTK"""
        issues = 0

        # Check for excessive exclamation marks
        if text_content.count('!') > text_content.count('.') * 2:
            issues += 2

        # Check for excessive capitalization
        words = text_content.split()
        capitalized_words = sum(1 for word in words if word.isupper() and len(word) > 3)
        if capitalized_words > len(words) * 0.15:
            issues += 2

        # Check for very short sentences (fragmented text)
        sentences = [s.strip() for s in text_content.split('.') if s.strip()]
        short_sentences = sum(1 for s in sentences if len(s.split()) < 3)
        if short_sentences > len(sentences) * 0.3:
            issues += 1

        return max(0, 100 - (issues * 15))

    def _analyze_formatting_consistency(self, structure_info: Dict[str, Any]) -> float:
        """Analyze formatting consistency"""
        try:
            layout_analysis = structure_info.get('layout_analysis', {})

            # Check if fonts are consistent across pages
            consistent_fonts = layout_analysis.get('consistent_fonts', True)

            # Check page count (too many pages might indicate template stuffing)
            page_count = structure_info.get('page_count', 1)
            if page_count > 10:
                return 60.0  # Suspiciously long resume
            elif page_count > 5:
                return 80.0
            else:
                return 90.0 if consistent_fonts else 70.0

        except Exception as e:
            logger.error(f"Formatting analysis failed: {str(e)}")
            return 75.0

    def _analyze_suspicious_patterns(self, text_content: str) -> float:
        """Look for patterns commonly found in fake resumes"""
        suspicious_indicators = 0
        total_indicators = 5

        # 1. Check for template-like repeated phrases
        repeated_phrases = self._find_repeated_phrases(text_content)
        if repeated_phrases > 3:
            suspicious_indicators += 1

        # 2. Check for placeholder text patterns
        placeholder_patterns = [
            r'\b(lorem ipsum|placeholder|sample text)\b',
            r'\b(experience|skill|achievement)\s+\d+\b',
            r'\b(placeholder|template|example)\b'
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, text_content, re.IGNORECASE):
                suspicious_indicators += 1

        # 3. Check for generic job titles
        generic_titles = [
            'software engineer', 'developer', 'manager', 'analyst', 'specialist'
        ]

        title_matches = sum(1 for title in generic_titles
                          if title.lower() in text_content.lower())
        if title_matches > 3:
            suspicious_indicators += 1

        # 4. Check for inconsistent date formats
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
        ]

        date_formats_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                date_formats_found.append(pattern)

        if len(date_formats_found) > 1:
            suspicious_indicators += 1

        # 5. Check for excessive bullet points (template-like structure)
        bullet_lines = text_content.count('•') + text_content.count('●') + text_content.count('■')
        total_lines = len([line for line in text_content.split('\n') if line.strip()])
        if total_lines > 0 and (bullet_lines / total_lines) > 0.7:
            suspicious_indicators += 1

        # Calculate score (inverse of suspicious indicators)
        return max(0, 100 - (suspicious_indicators / total_indicators * 100))

    def _find_repeated_phrases(self, text_content: str) -> int:
        """Find repeated phrases that might indicate template usage"""
        words = text_content.lower().split()
        if len(words) < 10:
            return 0

        # Look for repeated 3-word phrases
        phrases = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        phrase_counts = Counter(phrases)

        # Count phrases that appear more than twice
        repeated_count = sum(1 for count in phrase_counts.values() if count > 2)
        return min(repeated_count, 10)  # Cap at 10

    def _analyze_structure_consistency(self, structure_info: Dict[str, Any]) -> float:
        """Analyze overall document structure consistency"""
        try:
            # If we have page information, check consistency across pages
            pages_info = structure_info.get('font_analysis', {}).get('pages_info', [])

            if not pages_info:
                return 75.0  # Default if no page info available

            # Check if text length is consistent across pages
            text_lengths = [page.get('text_length', 0) for page in pages_info]

            if not text_lengths:
                return 75.0

            avg_length = sum(text_lengths) / len(text_lengths)
            variance = sum((length - avg_length) ** 2 for length in text_lengths) / len(text_lengths)

            # High variance might indicate inconsistent formatting
            if variance > avg_length * 0.5:
                return 60.0
            else:
                return 90.0

        except Exception as e:
            logger.error(f"Structure analysis failed: {str(e)}")
            return 75.0

    def _generate_analysis_details(self, scores: Dict[str, float], text_content: str) -> List[str]:
        """Generate detailed analysis feedback"""
        details = []

        if scores['font_consistency'] < 70:
            details.append("Multiple font types detected - consider standardizing fonts")
        elif scores['font_consistency'] > 90:
            details.append("Font usage is consistent across the document")

        if scores['grammar_quality'] < 60:
            details.append("Grammar issues detected - review for typos and sentence structure")
        elif scores['grammar_quality'] > 85:
            details.append("Good grammar and language quality")

        if scores['content_suspicious_patterns'] < 70:
            details.append("Some content patterns may indicate template usage")
        elif scores['content_suspicious_patterns'] > 85:
            details.append("Content appears original and authentic")

        if not details:
            details.append("Document structure analysis completed - no significant issues found")

        return details
