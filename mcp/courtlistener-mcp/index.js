import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

const COURTLISTENER_API_BASE = 'https://www.courtlistener.com/api/rest/v3';
const API_KEY = process.env.COURTLISTENER_API_KEY || '';

class CourtListenerMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'courtlistener-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
    this.axiosInstance = axios.create({
      baseURL: COURTLISTENER_API_BASE,
      headers: {
        'Authorization': API_KEY ? `Token ${API_KEY}` : undefined,
      },
    });
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'search_opinions',
          description: 'Search for court opinions and case law',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query for case law',
              },
              court: {
                type: 'string',
                description: 'Court identifier (optional)',
              },
              date_filed_after: {
                type: 'string',
                description: 'Filter cases filed after this date (YYYY-MM-DD)',
              },
              date_filed_before: {
                type: 'string',
                description: 'Filter cases filed before this date (YYYY-MM-DD)',
              },
              cited_gt: {
                type: 'number',
                description: 'Minimum number of citations',
              },
              page_size: {
                type: 'number',
                description: 'Number of results to return (max 100)',
                default: 20,
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'get_opinion',
          description: 'Get detailed information about a specific court opinion',
          inputSchema: {
            type: 'object',
            properties: {
              opinion_id: {
                type: 'string',
                description: 'The ID of the opinion to retrieve',
              },
            },
            required: ['opinion_id'],
          },
        },
        {
          name: 'search_cases',
          description: 'Search for docket entries and case information',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Search query for cases',
              },
              court: {
                type: 'string',
                description: 'Court identifier (optional)',
              },
              date_filed_after: {
                type: 'string',
                description: 'Filter cases filed after this date (YYYY-MM-DD)',
              },
              date_filed_before: {
                type: 'string',
                description: 'Filter cases filed before this date (YYYY-MM-DD)',
              },
              page_size: {
                type: 'number',
                description: 'Number of results to return (max 100)',
                default: 20,
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'get_case',
          description: 'Get detailed information about a specific case/docket',
          inputSchema: {
            type: 'object',
            properties: {
              docket_id: {
                type: 'string',
                description: 'The ID of the docket to retrieve',
              },
            },
            required: ['docket_id'],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'search_opinions':
            return await this.searchOpinions(args);
          case 'get_opinion':
            return await this.getOpinion(args);
          case 'search_cases':
            return await this.searchCases(args);
          case 'get_case':
            return await this.getCase(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error.message}`,
            },
          ],
        };
      }
    });
  }

  async searchOpinions(args) {
    const params = {
      q: args.query,
      court: args.court,
      filed_after: args.date_filed_after,
      filed_before: args.date_filed_before,
      cited_gt: args.cited_gt,
      page_size: args.page_size || 20,
    };

    const filteredParams = Object.fromEntries(
      Object.entries(params).filter(([_, v]) => v != null)
    );

    const response = await this.axiosInstance.get('/opinions/', { params: filteredParams });
    const data = response.data;

    const formattedResults = data.results.map((opinion) => ({
      id: opinion.id,
      case_name: opinion.case_name,
      court: opinion.court,
      date_filed: opinion.date_filed,
      citation_count: opinion.citation_count,
      excerpt: opinion.snippet || opinion.plain_text?.substring(0, 500),
      url: opinion.absolute_url,
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            total_count: data.count,
            results: formattedResults,
            next_page: data.next,
          }, null, 2),
        },
      ],
    };
  }

  async getOpinion(args) {
    const response = await this.axiosInstance.get(`/opinions/${args.opinion_id}/`);
    const opinion = response.data;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            id: opinion.id,
            case_name: opinion.case_name,
            court: opinion.court,
            date_filed: opinion.date_filed,
            citation_count: opinion.citation_count,
            judges: opinion.judges,
            type: opinion.type,
            citations: opinion.citations,
            plain_text: opinion.plain_text,
            html: opinion.html,
            url: opinion.absolute_url,
          }, null, 2),
        },
      ],
    };
  }

  async searchCases(args) {
    const params = {
      q: args.query,
      court: args.court,
      filed_after: args.date_filed_after,
      filed_before: args.date_filed_before,
      page_size: args.page_size || 20,
    };

    const filteredParams = Object.fromEntries(
      Object.entries(params).filter(([_, v]) => v != null)
    );

    const response = await this.axiosInstance.get('/dockets/', { params: filteredParams });
    const data = response.data;

    const formattedResults = data.results.map((docket) => ({
      id: docket.id,
      case_name: docket.case_name,
      court: docket.court,
      date_filed: docket.date_filed,
      docket_number: docket.docket_number,
      nature_of_suit: docket.nature_of_suit,
      url: docket.absolute_url,
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            total_count: data.count,
            results: formattedResults,
            next_page: data.next,
          }, null, 2),
        },
      ],
    };
  }

  async getCase(args) {
    const response = await this.axiosInstance.get(`/dockets/${args.docket_id}/`);
    const docket = response.data;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            id: docket.id,
            case_name: docket.case_name,
            court: docket.court,
            date_filed: docket.date_filed,
            docket_number: docket.docket_number,
            nature_of_suit: docket.nature_of_suit,
            jurisdiction_type: docket.jurisdiction_type,
            parties: docket.parties,
            assigned_to: docket.assigned_to,
            referred_to: docket.referred_to,
            url: docket.absolute_url,
          }, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('CourtListener MCP Server running...');
  }
}

const server = new CourtListenerMCPServer();
server.run().catch(console.error);