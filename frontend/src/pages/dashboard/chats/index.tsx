import { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from "react";
import {
  Box,
  // Container,
  VStack,
  HStack,
  Text,
  IconButton,
  Flex,
  Heading,
  useColorModeValue,
  Textarea,
  Divider,
  Button,
  Grid,
  GridItem,
  useBreakpointValue,
} from "@chakra-ui/react";
import { FiSend, FiRefreshCcw, FiPlusCircle } from "react-icons/fi";
import DashboardWrapper from "@/components/DashboardWrapper";
import { Chat, Message } from "@/types";
import { sampleChats } from "@/lib/chat-data";

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>("");
  const [chats] = useState<Chat[]>(sampleChats);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const bgColor = useColorModeValue("white", "gray.800");
  const borderColor = useColorModeValue("gray.200", "gray.600");
  const showSidebar = useBreakpointValue({ base: false, md: true });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  const hoverBg = useColorModeValue("gray.100", "gray.700");

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = () => {
    if (inputMessage.trim()) {
      setMessages([
        ...messages,
        { text: inputMessage, sender: "user", timestamp: new Date() },
      ]);
      setInputMessage("");
      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            text: "This is a sample AI response for trading insights.",
            sender: "ai",
            timestamp: new Date(),
          },
        ]);
      }, 1000);
    }
  };

  const handleKeyUp = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setInputMessage("");
  };

  return (
    <>
      <DashboardWrapper>
        <Grid
          templateColumns={{ base: "1fr", md: "250px 1fr" }}
          h="100vh"
          gap={4}
          p={4}
        >
          {showSidebar && (
            <GridItem>
              <VStack
                h="full"
                spacing={4}
                borderRight="1px"
                borderColor={borderColor}
                pr={4}
              >
                <Heading size="md">Chats</Heading>
                <VStack w="full" spacing={2} overflowY="auto">
                  {(() => {
                    return chats.map((chat) => (
                      <Box
                        key={chat.id}
                        w="full"
                        p={3}
                        borderRadius="md"
                        cursor="pointer"
                        _hover={{ bg: hoverBg }}
                      >
                        <Text fontWeight="bold">{chat.title}</Text>
                        <Text fontSize="sm" color="gray.500" noOfLines={1}>
                          {chat.lastMessage}
                        </Text>
                      </Box>
                    ));
                  })()}{" "}
                </VStack>
              </VStack>
            </GridItem>
          )}

          <GridItem>
            <VStack h="full" spacing={4}>
              <Flex w="full" justify="space-between" align="center">
                <Box>
                  <Heading size="xl" color="blue.500">
                    Nova Algo AI
                  </Heading>
                  <Text fontSize="lg" color="gray.500">
                    Your best AI trading Agent
                  </Text>
                </Box>
                <Button
                  leftIcon={<FiPlusCircle />}
                  colorScheme="blue"
                  onClick={handleNewChat}
                >
                  New Chat
                </Button>
              </Flex>

              <Flex
                direction="column"
                w="full"
                h="calc(100vh - 100px)"
                borderWidth="1px"
                borderRadius="lg"
                bg={bgColor}
                borderColor={borderColor}
              >
                <Box
                  flex="1"
                  overflowY="auto"
                  p={4}
                  css={{
                    "&::-webkit-scrollbar": {
                      width: "4px",
                    },
                    "&::-webkit-scrollbar-track": {
                      width: "6px",
                    },
                    "&::-webkit-scrollbar-thumb": {
                      background: useColorModeValue("gray.300", "gray.600"),
                      borderRadius: "24px",
                    },
                  }}
                >
                  {messages.map((message, index) => (
                    <Flex
                      key={index}
                      w="full"
                      justify={
                        message.sender === "user" ? "flex-end" : "flex-start"
                      }
                      mb={4}
                    >
                      <Box
                        maxW="70%"
                        bg={message.sender === "user" ? "blue.500" : "gray.100"}
                        color={message.sender === "user" ? "white" : "black"}
                        borderRadius="lg"
                        px={4}
                        py={2}
                      >
                        <Text>{message.text}</Text>
                        <Text
                          fontSize="xs"
                          color={
                            message.sender === "user"
                              ? "whiteAlpha.700"
                              : "gray.500"
                          }
                          mt={1}
                        >
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </Text>
                      </Box>
                    </Flex>
                  ))}
                  <div ref={messagesEndRef} />
                </Box>

                <Divider />

                <HStack
                  w="full"
                  p={4}
                  spacing={4}
                  bg={bgColor}
                  position={"sticky"}
                  bottom={0}
                >
                  <Textarea
                    value={inputMessage}
                    onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                      setInputMessage(e.target.value)
                    }
                    onKeyUp={handleKeyUp}
                    placeholder="Type your message here..."
                    resize="none"
                    rows={1}
                    borderRadius="lg"
                  />
                  <IconButton
                    colorScheme="blue"
                    aria-label="Send message"
                    icon={<FiSend />}
                    onClick={handleSendMessage}
                    isDisabled={!inputMessage.trim()}
                  />
                  <IconButton
                    aria-label="Clear chat"
                    icon={<FiRefreshCcw />}
                    onClick={() => setMessages([])}
                  />
                </HStack>
              </Flex>
            </VStack>
          </GridItem>
        </Grid>
      </DashboardWrapper>
    </>
  );
};

export default ChatInterface;
