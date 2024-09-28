import React, { useState, useEffect, ReactNode } from "react";
import {
  Box,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  PopoverCloseButton,
  useBreakpointValue,
  VStack,
  Heading,
  Portal,
  IconButton,
  HStack,
} from "@chakra-ui/react";
import { LuXCircle } from "react-icons/lu";

interface ResponsivePopoverSheetProps {
  title?: string;
  content: React.ReactNode;
  isOpen: boolean;
  onClose: () => void;
  onOpen: () => void;
  trigger: ReactNode;
}

export const ResponsivePopoverSheet: React.FC<ResponsivePopoverSheetProps> = ({
  isOpen,
  onClose,
  onOpen,
  title,
  content,

  trigger,
}) => {
  const [isPopover, setIsPopover] = useState(true);

  // Use Chakra's useBreakpointValue to determine if we should show a popover or sheet
  const variant = useBreakpointValue({ base: "sheet", md: "popover" });
  console.log("variant", variant);
  useEffect(() => {
    setIsPopover(variant === "popover");
  }, [variant]);
  console.log("isPopover", isPopover);
  // const handleToggle = () => {
  //   if (isPopover || !isOpen) {
  //     onToggle();
  //   }
  // };

  const renderContent = () => (
    <VStack align="stretch" spacing={4} p={4}>
      <Heading size="md">{title}</Heading>
      {content}
    </VStack>
  );
  useEffect(() => {
    if (!isPopover && isOpen) {
      document.body.style.overflow = "hidden";
    }
  });
  return (
    <>
      <Popover
        isOpen={isOpen && isPopover}
        onClose={onClose}
        onOpen={onOpen}
        closeOnBlur={true}
        placement="bottom"
        returnFocusOnClose={false}
      >
        <PopoverTrigger>
          <Box>{trigger}</Box>
        </PopoverTrigger>

        <PopoverContent borderRadius="md" boxShadow="lg">
          <PopoverArrow />
          <PopoverCloseButton />
          <PopoverBody>{renderContent()}</PopoverBody>
        </PopoverContent>
      </Popover>
      {!isPopover && isOpen && (
        <Portal>
          <Box
            h="100vh"
            w="100vw"
            position="fixed"
            top={0}
            left={0}
            bg={"blackAlpha.500"}
          >
            <Box
              p={4}
              color="white"
              mt="4"
              bg="white"
              roundedTop="24px"
              shadow="md"
              bottom={0}
              left={0}
              position="absolute"
              w={"full"}
              maxHeight="50vh"
              overflowY="auto"
              zIndex={1200}
            >
              <HStack justify={"flex-end"}>
                <IconButton
                  aria-label="Close"
                  variant={"ghost"}
                  icon={<LuXCircle size={24} />}
                  onClick={onClose}
                  colorScheme="blue"
                />
              </HStack>
              <VStack align="stretch" spacing={4}>
                <Heading size="md" color="gray.800">
                  {title}
                </Heading>
                <Box color="gray.800">{content}</Box>
              </VStack>
            </Box>
          </Box>
        </Portal>
      )}
    </>
  );
};
