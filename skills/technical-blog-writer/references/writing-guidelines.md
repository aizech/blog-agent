# Technical Writing Guidelines

This document provides additional context and examples for writing effective technical blog posts.

## Audience analysis

### Technical levels
- **Beginner**: New to programming or the specific domain
- **Intermediate**: Familiar with basics but not advanced concepts
- **Advanced**: Experienced practitioners looking for depth
- **Mixed**: Varying levels of technical expertise

### Writing for mixed audiences
- Start with the problem everyone can understand
- Layer technical details progressively
- Provide optional deep-dive sections
- Use clear section headers for navigation

## Structure patterns

### Problem-first approach
1. Start with a relatable problem
2. Explain why it matters
3. Present the solution
4. Show implementation
5. Discuss tradeoffs

### Concept-first approach
1. Introduce the core concept
2. Explain its significance
3. Show practical applications
4. Provide implementation details
5. Cover limitations and alternatives

## Code example guidelines

### When to include code
- To demonstrate a specific technique
- When code is clearer than prose
- For showing actual implementation
- To illustrate patterns or anti-patterns

### Code quality standards
- Use meaningful variable names
- Add explanatory comments
- Show only relevant portions
- Include error handling when important
- Provide context for usage

### Code formatting
```python
# Good: Clear variable names and comments
def calculate_user_engagement(user_actions, time_window):
    """Calculate engagement score based on user actions"""
    if not user_actions:
        return 0.0
    
    # Weight recent actions more heavily
    weighted_score = 0
    for action in user_actions:
        time_weight = decay_function(action.timestamp, time_window)
        weighted_score += action.value * time_weight
    
    return weighted_score / len(user_actions)
```

## Research best practices

### Source evaluation criteria
- **Authority**: Is the source recognized in the field?
- **Recency**: Is the information current?
- **Accuracy**: Are claims supported by evidence?
- **Relevance**: Does it address your specific topic?

### Research workflow
1. **Broad exploration**: Understand the topic landscape
2. **Targeted research**: Dive into specific aspects
3. **Source verification**: Cross-check important claims
4. **Synthesis**: Combine insights from multiple sources

## Common writing mistakes

### Overly technical writing
- Using jargon without explanation
- Assuming prior knowledge
- Focusing on implementation over concepts
- Neglecting the "why" behind technical choices

### Under-explained concepts
- Introducing terms without definition
- Showing code without context
- Making logical leaps without justification
- Ignoring audience's knowledge gaps

### Poor structure
- Missing clear problem statement
- Illogical flow between sections
- Buried key insights
- Weak or missing conclusions

## Quality indicators

### Signs of effective technical writing
- Clear problem statement
- Logical progression of ideas
- Appropriate technical depth
- Concrete examples and analogies
- Actionable takeaways

### Signs that need improvement
- Vague or generic descriptions
- Unclear audience targeting
- Missing context or background
- Poorly explained code examples
- Weak conclusions or next steps

## Anthropic-style voice transformation

### From instructional to experiential

We've found that transforming our writing from instructional to experiential voice makes it more authentic and helpful. Here's how we approach it:

**Before (Instructional):**
- "You should implement proper error handling"
- "The best practice is to validate inputs"
- "Developers must consider performance implications"

**After (Experiential):**
- "We've learned that implementing proper error handling saves us hours of debugging"
- "We've found that validating inputs prevents the most common issues we encounter"
- "We've discovered that performance implications often surprise us, so we always measure"

### Our voice patterns

**Sharing decisions:**
- "We've made a choice to..."
- "We've decided that..."
- "We've learned that..."

**Explaining reasoning:**
- "We chose this approach because..."
- "We've discovered that..."
- "We've found that..."

**Being transparent:**
- "We're still figuring out..."
- "We don't have all the answers, but..."
- "We've made mistakes and here's what we learned..."

### Examples from our experience

**Technical explanations:**
- "When we first implemented this, we assumed..."
- "We've tried several approaches and here's what worked for us..."
- "We've discovered that the documentation doesn't cover this edge case..."

**Problem-solving:**
- "We faced this challenge when..."
- "Our team struggled with this until we realized..."
- "We've seen this pattern repeatedly in our projects..."

**Recommendations:**
- "We recommend this because we've seen..."
- "We've stopped doing X because we found..."
- "We've started doing Y after we learned..."

## Voice variation and anti-patterns

### Repetitive "we've" patterns to avoid

**Problematic repetition:**
- "We've found that... We've learned that... We've discovered that... We've seen that..."
- Every paragraph starting with "We've..." or "We have..."
- Consistent sentence structure: "We've [verb] that..." repeated throughout

**Natural alternatives:**
- Mix direct statements: "The tests showed..." instead of "We've found that the tests showed..."
- Vary expressions: "What surprised us was...", "Our team discovered...", "Here's what worked..."
- Use different sentence starters: "In our experience...", "What we learned was...", "The key insight was..."

### Before/After examples

**Before (repetitive):**
> We've found that authentication is crucial. We've learned that OAuth 2.1 works best. We've discovered that token validation prevents attacks. We've seen that many teams skip this step. We've experienced the consequences of weak security.

**After (natural):**
> Authentication is crucial. Our tests showed that OAuth 2.1 works best, and we discovered token validation prevents attacks. Many teams skip this step—we learned the hard way that weak security has serious consequences.

### Voice variation techniques

**1. Mix direct statements with team perspective:**
- Instead of: "We've found that caching improves performance"
- Try: "Caching improves performance. Our tests showed a 40% speed increase."

**2. Vary sentence length and structure:**
- Short: "Security matters."
- Medium: "We learned that security matters because attacks are common."
- Long: "What surprised us was how many teams overlook basic security measures, even when they know attacks are common."

**3. Use specific, concrete details:**
- Instead of: "We've seen many issues"
- Try: "We've seen three types of attacks: injection, bypass, and data exfiltration"

**4. Sound like you're talking to colleagues:**
- Instead of: "We've determined that the optimal approach is..."
- Try: "Here's what worked for us..." or "The approach that saved us was..."

## FAQ section best practices

### Purpose of FAQs

FAQ sections serve multiple purposes:
- Address common reader questions proactively
- Clarify complex or confusing points
- Provide practical implementation guidance
- Handle edge cases and "what if" scenarios
- Improve SEO by targeting question-based searches

### Question identification strategies

**From content analysis:**
- Look for concepts that required detailed explanation
- Identify points where readers might get stuck
- Consider alternative approaches or scenarios
- Think about prerequisites and assumptions

**From reader perspective:**
- What would confuse someone new to this topic?
- What practical barriers might they encounter?
- What follow-up questions would naturally arise?
- What alternatives might they consider?

### FAQ writing techniques

**Question formulation:**
- Use clear, specific language
- Avoid overly broad or vague questions
- Frame from reader's perspective
- Focus on actionable or clarifying information

**Answer structure:**
- Start with direct answer
- Provide brief explanation if needed
- Reference main article sections when helpful
- Keep answers concise (1-3 sentences typically)

**Integration with article:**
- Ensure FAQs don't repeat main content verbatim
- Use FAQs to address points that didn't fit in main flow
- Cross-reference to maintain article cohesion
- Place after key takeaways for natural flow

### Common FAQ types

**Clarification questions:**
- "What's the difference between X and Y?"
- "How does this relate to [related concept]?"

**Implementation questions:**
- "How do I get started with this?"
- "What tools do I need?"

**Troubleshooting questions:**
- "What if [common problem] occurs?"
- "How do I handle [edge case]?"

**Comparison questions:**
- "When should I use this instead of [alternative]?"
- "What are the tradeoffs?"

### FAQ quality indicators

**Effective FAQs:**
- Address genuine reader concerns
- Provide new information beyond main content
- Are concise and directly answer the question
- Reference relevant article sections appropriately

**Poor FAQs:**
- Repeat information already covered in detail
- Are too vague or generic
- Don't add value to the reader experience
- Are overly numerous or unfocused
