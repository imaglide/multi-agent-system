# Multi-Agent System Architecture

## Overview

This document describes the architecture of the multi-agent system, a collaborative AI framework where specialized agents work together to solve complex tasks.

## Core Principles

1. **Separation of Concerns**: Each agent specializes in a specific capability
2. **Asynchronous Communication**: Non-blocking message passing between agents
3. **Loose Coupling**: Agents communicate only through the message bus
4. **Extensibility**: Easy to add new agent types
5. **Fault Tolerance**: Agent failures don't crash the entire system

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Message Bus (Central Hub)                │
│  - Message routing                                           │
│  - Agent registration                                        │
│  - Communication history                                     │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│ Manager Agent  │  │Research Agent│  │ Writer Agent   │
│ (Coordinator)  │  │ (Gatherer)   │  │ (Creator)      │
└────────────────┘  └──────────────┘  └────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Analyzer Agent │
                    │ (Insights)     │
                    └────────────────┘
```

## Components

### 1. Communication Layer

#### Message (`communication/message.py`)
- **Purpose**: Encapsulates all inter-agent communication
- **Key Features**:
  - Typed messages (TASK, RESULT, REQUEST, RESPONSE, etc.)
  - Correlation IDs for tracking related messages
  - Timestamps and metadata
  - Reply convenience method

#### MessageBus (`communication/message_bus.py`)
- **Purpose**: Central message routing infrastructure
- **Key Features**:
  - Agent registration/unregistration
  - Point-to-point message delivery
  - Broadcast capabilities
  - Message history tracking
  - Thread-safe operations with asyncio locks

#### Protocol (`communication/protocol.py`)
- **Purpose**: Defines standard message formats
- **Key Features**:
  - Task representation
  - Agent status structures
  - Standard request/response formats
  - Agent capabilities enumeration

#### Coordinator (`communication/coordination.py`)
- **Purpose**: Orchestration utilities for complex workflows
- **Key Features**:
  - Task assignment tracking
  - Result aggregation
  - Agent status collection
  - Timeout management

### 2. Agent Framework

#### BaseAgent (`agents/base_agent.py`)
- **Purpose**: Abstract base class for all agents
- **Key Features**:
  - Async message processing loop
  - Inbox queue management
  - Lifecycle management (start/stop)
  - Message routing to handlers
  - Status reporting

**Agent Lifecycle**:
```
create → start → [process messages] → stop
```

### 3. Specialized Agents

#### ManagerAgent (`agents/manager/coordinator.py`)
- **Role**: Task coordinator and orchestrator
- **Capabilities**:
  - Task decomposition
  - Agent selection based on capabilities
  - Result synthesis
  - Workflow management

**Workflow**:
```
Complex Task → Decompose → Assign to Specialists → Gather Results → Synthesize
```

#### ResearchAgent (`agents/research/gatherer.py`)
- **Role**: Information gathering and verification
- **Capabilities**:
  - Multi-source search
  - Information cross-checking
  - Confidence scoring
  - Knowledge base management

**Features**:
- Simulated web search
- Academic database queries
- Knowledge base integration
- Reliability weighting

#### WriterAgent (`agents/writer/creator.py`)
- **Role**: Content creation and structuring
- **Capabilities**:
  - Multiple content types (articles, reports, etc.)
  - Style adaptation (formal, casual, etc.)
  - Research integration
  - Analysis integration

**Content Structure**:
- Introduction
- Research-based sections
- Analysis-based sections
- Conclusion

#### AnalyzerAgent (`agents/analyzer/insights.py`)
- **Role**: Data analysis and insight extraction
- **Capabilities**:
  - Pattern detection
  - Statistical analysis
  - Insight extraction
  - Visualization recommendations

**Analysis Types**:
- Structure analysis
- Type distribution
- Numeric statistics
- Trend detection

## Communication Patterns

### 1. Task Delegation
```
Manager → [TASK] → Specialist Agent
Specialist Agent → [RESULT] → Manager
```

### 2. Information Request
```
Agent A → [REQUEST] → Agent B
Agent B → [RESPONSE] → Agent A
```

### 3. Broadcast
```
Agent → [BROADCAST] → All Other Agents
```

### 4. Status Check
```
Coordinator → [STATUS] → Agent
Agent → [STATUS_RESPONSE] → Coordinator
```

## Message Flow Example

**Task**: "Research and write a report on climate change"

```
1. User → Manager: TASK(description="Research and write...")
2. Manager decomposes into:
   - Subtask 1: Research
   - Subtask 2: Analyze
   - Subtask 3: Write
3. Manager → Research Agent: TASK(subtask_1)
4. Manager → Analyzer Agent: TASK(subtask_2)
5. Manager → Writer Agent: TASK(subtask_3)
6. Research Agent → Manager: RESULT(research_data)
7. Analyzer Agent → Manager: RESULT(analysis_data)
8. Writer Agent → Manager: RESULT(content)
9. Manager synthesizes results
10. Manager → User: RESULT(final_report)
```

## Extensibility

### Adding a New Agent

1. **Create agent class** inheriting from `BaseAgent`
2. **Implement** `process_task()` method
3. **Define capabilities** in constructor
4. **Register** with message bus
5. **Update** manager's agent selection logic

Example:
```python
class CustomAgent(BaseAgent):
    def __init__(self, message_bus: MessageBus):
        super().__init__(
            agent_id="custom_agent",
            message_bus=message_bus,
            capabilities=["custom_capability"]
        )

    async def process_task(self, task_data: Dict[str, Any]) -> Any:
        # Custom processing logic
        return result
```

### Adding New Message Types

1. Add to `MessageType` enum in `message.py`
2. Implement handler in `BaseAgent._handle_message()`
3. Update protocol definitions if needed

## Error Handling

### Agent-Level Errors
- Caught in `_handle_message()`
- Error message sent back to sender
- Agent remains operational

### Task-Level Errors
- Timeout mechanisms in coordinator
- Failed task status tracking
- Partial result handling

### System-Level Errors
- Agent crash doesn't affect message bus
- Message bus failures handled gracefully
- Restart capabilities

## Performance Considerations

### Async Operations
- All I/O operations are async
- Non-blocking message processing
- Concurrent task handling

### Message Queue Management
- Bounded queues prevent memory issues
- Message history limits
- Periodic cleanup

### Scalability
- Horizontal: Add more agent instances
- Vertical: Increase agent capabilities
- Distributed: Message bus can be replaced with networked solution

## Security Considerations

### Message Validation
- Type checking on message content
- Agent ID verification
- Correlation ID validation

### Resource Limits
- Task timeouts
- Queue size limits
- Message size limits

### Isolation
- Agents operate in separate async contexts
- No shared state between agents
- Message-only communication

## Testing Strategy

### Unit Tests
- Individual agent functionality
- Message creation and routing
- Protocol compliance

### Integration Tests
- Multi-agent workflows
- End-to-end task completion
- Message bus operations

### Performance Tests
- Concurrent task handling
- Message throughput
- Latency measurements

## Future Enhancements

1. **Distributed Deployment**
   - Replace in-memory message bus with Redis/RabbitMQ
   - Network-based agent communication
   - Load balancing

2. **Persistence**
   - Task state persistence
   - Message history storage
   - Agent knowledge base persistence

3. **Monitoring**
   - Real-time dashboard
   - Performance metrics
   - Agent health monitoring

4. **LLM Integration**
   - Anthropic Claude API integration
   - Enhanced content generation
   - Intelligent task decomposition

5. **Advanced Coordination**
   - Consensus mechanisms
   - Voting systems
   - Conflict resolution

## References

- [Multi-Agent Systems (Wooldridge)](https://www.cs.ox.ac.uk/people/michael.wooldridge/pubs/imas/IMAS2e.html)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Message-Oriented Middleware](https://en.wikipedia.org/wiki/Message-oriented_middleware)
